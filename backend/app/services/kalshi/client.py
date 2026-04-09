from __future__ import annotations

import base64
import logging
import random
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock
from urllib.parse import urlparse

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from app.config import Settings
from app.services.kalshi.types import KalshiCandlestick, KalshiMarket

logger = logging.getLogger(__name__)
_DEFAULT_READ_REQUESTS_PER_SECOND = 8
_RATE_LIMIT_RETRY_ATTEMPTS = 3
_RATE_LIMIT_BASE_DELAY_SECONDS = 0.5
_RATE_LIMIT_MAX_DELAY_SECONDS = 4.0


def _to_unix(timestamp: str) -> int:
    return int(datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp())


class _RequestRateLimiter:
    def __init__(self, requests_per_second: int):
        self._interval_seconds = 1 / max(1, requests_per_second)
        self._next_request_at = 0.0
        self._lock = Lock()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            wait_seconds = max(0.0, self._next_request_at - now)
            if wait_seconds > 0:
                time.sleep(wait_seconds)
                now = time.monotonic()
            self._next_request_at = max(self._next_request_at, now) + self._interval_seconds


@dataclass(frozen=True)
class KalshiMarketBundle:
    raw_market: KalshiMarket
    candlesticks: list[KalshiCandlestick]
    history_source: str


class KalshiClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._base_url = settings.kalshi_api_base_url.rstrip("/")
        self._parsed_base = urlparse(self._base_url)
        self._base_path = self._parsed_base.path.rstrip("/")
        self._session = requests.Session()
        self._private_key = self._load_private_key()
        self._lock = Lock()
        self._read_rate_limiter = _RequestRateLimiter(_DEFAULT_READ_REQUESTS_PER_SECOND)

    def _load_private_key(self):
        with open(self._settings.kalshi_private_key_path, "rb") as handle:
            return serialization.load_pem_private_key(handle.read(), password=None)

    def _signed_headers(self, method: str, path: str) -> dict[str, str]:
        timestamp = str(int(time.time() * 1000))
        message = f"{timestamp}{method.upper()}{path}".encode("utf-8")
        signature = self._private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )
        return {
            "KALSHI-ACCESS-KEY": self._settings.kalshi_api_key,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "KALSHI-ACCESS-SIGNATURE": base64.b64encode(signature).decode("utf-8"),
        }

    def _request_delay_seconds(self, response: requests.Response | None, attempt: int) -> float:
        if response is not None:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return max(float(retry_after), 0.0)
                except ValueError:
                    pass

        base_delay = min(_RATE_LIMIT_BASE_DELAY_SECONDS * (2**attempt), _RATE_LIMIT_MAX_DELAY_SECONDS)
        return round(base_delay + random.uniform(0, min(base_delay * 0.25, 0.25)), 3)

    def _request(self, method: str, path: str, *, params: dict[str, object] | None = None, auth: bool = False) -> dict:
        url = f"{self._base_url}{path}"
        headers = {"Accept": "application/json"}
        if auth:
            headers.update(self._signed_headers(method, f"{self._base_path}{path}"))

        for attempt in range(_RATE_LIMIT_RETRY_ATTEMPTS + 1):
            self._read_rate_limiter.acquire()
            response = self._session.request(method, url, params=params, headers=headers, timeout=20)
            try:
                response.raise_for_status()
                return response.json()
            except requests.HTTPError as exc:
                status_code = exc.response.status_code if exc.response is not None else None
                if status_code != 429 or attempt >= _RATE_LIMIT_RETRY_ATTEMPTS:
                    raise
                delay_seconds = self._request_delay_seconds(exc.response, attempt)
                logger.warning(
                    "Kalshi rate limit for %s %s; retrying in %.2fs (attempt %s/%s).",
                    method.upper(),
                    path,
                    delay_seconds,
                    attempt + 1,
                    _RATE_LIMIT_RETRY_ATTEMPTS,
                )
                time.sleep(delay_seconds)

        raise RuntimeError(f"Kalshi request retry loop exhausted for {method.upper()} {path}")

    def list_markets(self, *, limit: int, status: str) -> list[KalshiMarket]:
        payload = self._request("GET", "/markets", params={"limit": limit, "status": status})
        return payload.get("markets", [])

    def list_historical_markets(self, *, limit: int) -> list[KalshiMarket]:
        payload = self._request("GET", "/historical/markets", params={"limit": limit})
        return payload.get("markets", [])

    def get_market(self, ticker: str) -> KalshiMarket | None:
        payload = self._request("GET", "/markets", params={"tickers": ticker})
        markets = payload.get("markets", [])
        return markets[0] if markets else None

    def get_historical_market(self, ticker: str) -> KalshiMarket | None:
        payload = self._request("GET", "/historical/markets", params={"tickers": ticker})
        markets = payload.get("markets", [])
        return markets[0] if markets else None

    def get_market_candlesticks(
        self,
        *,
        market: KalshiMarket,
        history_window_days: int,
    ) -> tuple[list[KalshiCandlestick], str]:
        end_ts = int(datetime.now(UTC).timestamp())
        created_ts = _to_unix(market["created_time"])
        close_ts = _to_unix(market["close_time"])
        start_ts = max(created_ts, end_ts - history_window_days * 24 * 60 * 60)
        status = market.get("status", "")

        if status in {"determined", "disputed", "amended", "finalized"}:
            end_ts = _to_unix(market.get("settlement_ts") or market["close_time"])
            start_ts = max(created_ts, end_ts - history_window_days * 24 * 60 * 60)
            payload = self._request(
                "GET",
                f"/historical/markets/{market['ticker']}/candlesticks",
                params={
                    "start_ts": start_ts,
                    "end_ts": end_ts,
                    "period_interval": 1440 if history_window_days > 14 else 60,
                },
            )
            return payload.get("candlesticks", []), "historical"

        event_ticker = market.get("event_ticker") or market["ticker"].rsplit("-", 1)[0]
        payload = self._request(
            "GET",
            f"/series/{event_ticker}/markets/{market['ticker']}/candlesticks",
            params={
                "start_ts": start_ts,
                "end_ts": min(end_ts, close_ts),
                "period_interval": 1440 if history_window_days > 14 else 60,
                "include_latest_before_start": True,
            },
        )
        return payload.get("candlesticks", []), "live"

    def get_market_bundle(
        self,
        raw_market: KalshiMarket,
        *,
        history_window_days: int | None = None,
    ) -> KalshiMarketBundle:
        try:
            candlesticks, history_source = self.get_market_candlesticks(
                market=raw_market,
                history_window_days=history_window_days or self._settings.history_window_days,
            )
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code != 429:
                raise
            logger.warning(
                "Kalshi candlestick request rate-limited for %s; using synthetic fallback history.",
                raw_market["ticker"],
            )
            candlesticks, history_source = [], "rate_limited"
        return KalshiMarketBundle(
            raw_market=raw_market,
            candlesticks=candlesticks,
            history_source=history_source,
        )

    def verify_credentials(self) -> dict:
        with self._lock:
            return self._request("GET", "/portfolio/balance", auth=True)
