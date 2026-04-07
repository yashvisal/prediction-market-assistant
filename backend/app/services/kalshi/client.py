from __future__ import annotations

import base64
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


def _to_unix(timestamp: str) -> int:
    return int(datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp())


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

    def _request(self, method: str, path: str, *, params: dict[str, object] | None = None, auth: bool = False) -> dict:
        url = f"{self._base_url}{path}"
        headers = {"Accept": "application/json"}
        if auth:
            headers.update(self._signed_headers(method, f"{self._base_path}{path}"))

        response = self._session.request(method, url, params=params, headers=headers, timeout=20)
        response.raise_for_status()
        return response.json()

    def list_markets(self, *, limit: int, status: str) -> list[KalshiMarket]:
        payload = self._request("GET", "/markets", params={"limit": limit, "status": status})
        return payload.get("markets", [])

    def list_historical_markets(self, *, limit: int) -> list[KalshiMarket]:
        payload = self._request("GET", "/historical/markets", params={"limit": limit})
        return payload.get("markets", [])

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

    def get_market_bundle(self, raw_market: KalshiMarket) -> KalshiMarketBundle:
        candlesticks, history_source = self.get_market_candlesticks(
            market=raw_market,
            history_window_days=self._settings.history_window_days,
        )
        return KalshiMarketBundle(
            raw_market=raw_market,
            candlesticks=candlesticks,
            history_source=history_source,
        )

    def verify_credentials(self) -> dict:
        with self._lock:
            return self._request("GET", "/portfolio/balance", auth=True)
