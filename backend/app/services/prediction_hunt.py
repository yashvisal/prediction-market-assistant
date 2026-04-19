from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from app.models.prediction_hunt import (
    PredictionHuntCandle,
    PredictionHuntDeskSnapshotResponse,
    PredictionHuntEventSummary,
    PredictionHuntEventsResponse,
    PredictionHuntMarketSummary,
    PredictionHuntMarketsResponse,
    PredictionHuntMatchingEvent,
    PredictionHuntMatchingGroup,
    PredictionHuntMatchingMarket,
    PredictionHuntMatchingMarketsResponse,
    PredictionHuntMatchGroupSummary,
    PredictionHuntOrderbookLevel,
    PredictionHuntOrderbookResponse,
    PredictionHuntOrderbookSide,
    PredictionHuntPlatformStatus,
    PredictionHuntPriceHistoryResponse,
    PredictionHuntPriceSnapshot,
    PredictionHuntRateLimitSnapshot,
    PredictionHuntStatusResponse,
)


class PredictionHuntNotConfiguredError(RuntimeError):
    pass


class PredictionHuntUpstreamError(RuntimeError):
    def __init__(self, *, path: str, status_code: int, detail: str | None = None) -> None:
        self.path = path
        self.status_code = status_code
        self.detail = detail or f"Prediction Hunt returned {status_code} for {path}."
        super().__init__(self.detail)


@dataclass(frozen=True)
class _ApiResult:
    payload: dict[str, Any]
    rate_limits: PredictionHuntRateLimitSnapshot | None


_CACHE: dict[str, tuple[float, _ApiResult]] = {}
_THROTTLE_LOCK = threading.Lock()


def clear_prediction_hunt_http_cache() -> None:
    """Drop cached HTTP responses (e.g. after a failed /markets load that should retry fresh)."""
    _CACHE.clear()
_NEXT_REQUEST_AT = 0.0
LOGGER = logging.getLogger(__name__)

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_PATH, override=False)


class PredictionHuntClient:
    def __init__(self) -> None:
        self._api_key = os.getenv("PREDICTION_HUNT_API_KEY")
        self._base_url = os.getenv("PREDICTION_HUNT_API_URL", "https://www.predictionhunt.com/api/v2").rstrip("/")
        self._min_interval_seconds = float(os.getenv("PREDICTION_HUNT_MIN_INTERVAL_SECONDS", "1.05"))
        self._session = requests.Session()

    def list_events(
        self,
        *,
        limit: int = 6,
        status: str = "active",
        event_type: str | None = None,
        q: str | None = None,
        cursor: str | None = None,
    ) -> _ApiResult:
        params: dict[str, object] = {"limit": limit, "status": status}
        if event_type:
            params["event_type"] = event_type
        if q:
            params["q"] = q
        if cursor:
            params["cursor"] = cursor
        return self._get("/events", params=params)

    def list_markets(
        self,
        *,
        limit: int = 8,
        status: str = "active",
        platform: str | None = None,
        category: str | None = None,
        q: str | None = None,
        cursor: str | None = None,
    ) -> _ApiResult:
        params: dict[str, object] = {"limit": limit, "status": status}
        if platform:
            params["platform"] = platform
        if category:
            params["category"] = category
        if q:
            params["q"] = q
        if cursor:
            params["cursor"] = cursor
        return self._get("/markets", params=params)

    def get_matching_markets(
        self,
        *,
        q: str | None = None,
        polymarket_key: str | None = None,
    ) -> _ApiResult:
        params = {"q": q, "polymarket_key": polymarket_key}
        provided = [value for value in params.values() if value]
        if len(provided) != 1:
            raise ValueError("Provide exactly one of q or polymarket_key.")
        clean_params = {key: value for key, value in params.items() if value}
        return self._get("/matching-markets", params=clean_params)

    def get_price_history(
        self,
        *,
        platform: str,
        market_id: str,
        from_iso: str | None = None,
        to_iso: str | None = None,
        interval: str = "1h",
    ) -> _ApiResult:
        params: dict[str, object] = {"platform": platform, "market_id": market_id, "interval": interval}
        if from_iso:
            params["from"] = from_iso
        if to_iso:
            params["to"] = to_iso
        return self._get("/prices/history", params=params)

    def get_orderbook(self, *, platform: str, market_id: str) -> _ApiResult:
        return self._get("/orderbook", params={"platform": platform, "market_id": market_id})

    def get_status(self) -> _ApiResult:
        return self._get("/status", key_required=False)

    def _get(
        self,
        path: str,
        *,
        params: dict[str, object] | None = None,
        key_required: bool = True,
    ) -> _ApiResult:
        if key_required and not self._api_key:
            raise PredictionHuntNotConfiguredError("Missing PREDICTION_HUNT_API_KEY.")

        cache_key = json.dumps({"path": path, "params": params or {}}, sort_keys=True, default=str)
        now = time.time()
        cached = _CACHE.get(cache_key)
        if cached and cached[0] > now:
            return cached[1]

        headers = {"Accept": "application/json"}
        if self._api_key:
            headers["X-API-Key"] = self._api_key

        with _THROTTLE_LOCK:
            global _NEXT_REQUEST_AT

            cached = _CACHE.get(cache_key)
            if cached and cached[0] > time.time():
                return cached[1]

            wait_seconds = max(0.0, _NEXT_REQUEST_AT - time.time())
            if wait_seconds > 0:
                time.sleep(wait_seconds)

            response = self._session.get(
                f"{self._base_url}{path}",
                params=params,
                headers=headers,
                timeout=20,
            )
            _NEXT_REQUEST_AT = time.time() + self._min_interval_seconds

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            LOGGER.warning(
                "prediction_hunt_upstream_error path=%s status=%s",
                path,
                response.status_code,
            )
            if response.status_code == 429 and cached:
                return cached[1]
            raise PredictionHuntUpstreamError(
                path=path,
                status_code=response.status_code,
                detail=_build_upstream_detail(path, response),
            ) from exc

        result = _ApiResult(
            payload=response.json(),
            rate_limits=_extract_rate_limits(response.headers),
        )
        _CACHE[cache_key] = (time.time() + _ttl_for_path(path), result)
        return result


def get_prediction_hunt_events(
    *,
    limit: int = 6,
    status: str = "active",
    event_type: str | None = None,
    q: str | None = None,
    cursor: str | None = None,
) -> PredictionHuntEventsResponse:
    result = _client().list_events(
        limit=limit,
        status=status,
        event_type=event_type,
        q=q,
        cursor=cursor,
    )
    payload = result.payload
    events = [_to_event_summary(item) for item in payload.get("events", [])]
    return PredictionHuntEventsResponse(
        events=_sorted_prediction_hunt_events(events),
        nextCursor=payload.get("next_cursor"),
        totalCount=int(payload.get("total_count") or 0),
        rateLimits=result.rate_limits,
    )


def get_prediction_hunt_markets(
    *,
    limit: int = 8,
    status: str = "active",
    platform: str | None = None,
    category: str | None = None,
    q: str | None = None,
    cursor: str | None = None,
) -> PredictionHuntMarketsResponse:
    result = _client().list_markets(
        limit=limit,
        status=status,
        platform=platform,
        category=category,
        q=q,
        cursor=cursor,
    )
    payload = result.payload
    markets = [_to_market_summary(item) for item in payload.get("markets", [])]
    return PredictionHuntMarketsResponse(
        markets=_sorted_prediction_hunt_markets(markets),
        nextCursor=payload.get("next_cursor"),
        totalCount=int(payload.get("total_count") or 0),
        rateLimits=result.rate_limits,
    )


def get_prediction_hunt_matching_markets(
    *,
    q: str | None = None,
    polymarket_key: str | None = None,
) -> PredictionHuntMatchingMarketsResponse:
    result = _client().get_matching_markets(
        q=q,
        polymarket_key=polymarket_key,
    )
    payload = result.payload
    events = [_to_matching_event(item) for item in payload.get("events", [])]
    return PredictionHuntMatchingMarketsResponse(
        success=bool(payload.get("success")),
        count=int(payload.get("count") or 0),
        events=_sorted_prediction_hunt_matching_events(events),
        rateLimits=result.rate_limits,
    )


def get_prediction_hunt_price_history(
    *,
    platform: str,
    market_id: str,
    from_iso: str | None = None,
    to_iso: str | None = None,
    interval: str = "1h",
) -> PredictionHuntPriceHistoryResponse:
    result = _client().get_price_history(
        platform=platform,
        market_id=market_id,
        from_iso=from_iso,
        to_iso=to_iso,
        interval=interval,
    )
    payload = result.payload
    return PredictionHuntPriceHistoryResponse(
        marketId=str(payload.get("market_id") or market_id),
        platform=str(payload.get("platform") or platform),
        interval=str(payload.get("interval") or interval),
        candles=[_to_candle(item) for item in payload.get("candles", [])],
        rateLimits=result.rate_limits,
    )


def get_prediction_hunt_orderbook(*, platform: str, market_id: str) -> PredictionHuntOrderbookResponse:
    result = _client().get_orderbook(platform=platform, market_id=market_id)
    payload = result.payload
    return PredictionHuntOrderbookResponse(
        marketId=str(payload.get("market_id") or market_id),
        platform=str(payload.get("platform") or platform),
        timestamp=payload.get("timestamp"),
        yes=_to_orderbook_side(payload.get("yes")),
        no=_to_orderbook_side(payload.get("no")),
        rateLimits=result.rate_limits,
    )


def get_prediction_hunt_status() -> PredictionHuntStatusResponse:
    result = _client().get_status()
    payload = result.payload
    raw_platforms = payload.get("platforms", {}) or {}
    return PredictionHuntStatusResponse(
        status=str(payload.get("status") or "unknown"),
        platforms={str(name): _to_platform_status(item) for name, item in raw_platforms.items()},
        rateLimits=result.rate_limits,
    )


def get_prediction_hunt_desk_snapshot(
    *,
    events_limit: int = 6,
    markets_limit: int = 8,
    events_status: str = "active",
    markets_status: str = "active",
    market_platform: str | None = None,
    market_category: str | None = None,
    market_query: str | None = None,
    selected_market_id: str | None = None,
    selected_market_platform: str | None = None,
    match_query: str | None = None,
    history_interval: str = "1h",
) -> PredictionHuntDeskSnapshotResponse:
    warnings: list[str] = []
    status = get_prediction_hunt_status()
    try:
        events = get_prediction_hunt_events(limit=events_limit, status=events_status, q=market_query)
    except PredictionHuntUpstreamError as exc:
        if exc.path == "/events" and exc.status_code in {401, 403}:
            events = PredictionHuntEventsResponse(events=[], nextCursor=None, totalCount=0, rateLimits=None)
            warnings.append(exc.detail)
        else:
            raise
    markets = get_prediction_hunt_markets(
        limit=markets_limit,
        status=markets_status,
        platform=market_platform,
        category=market_category,
    )
    searched_markets = (
        get_prediction_hunt_markets(
            limit=markets_limit,
            status=markets_status,
            platform=market_platform,
            category=market_category,
            q=market_query,
        )
        if market_query
        else None
    )
    effective_match_query = match_query or market_query

    selected_market = _select_market(
        (searched_markets.markets if searched_markets else []) + markets.markets,
        market_id=selected_market_id,
        platform=selected_market_platform,
    )
    history = None
    orderbook = None
    matching = None

    if selected_market:
        try:
            history = get_prediction_hunt_price_history(
                platform=selected_market.platform,
                market_id=selected_market.marketId,
                interval=history_interval,
            )
        except PredictionHuntUpstreamError as exc:
            warnings.append(exc.detail)

    if selected_market and selected_market.platform in {"polymarket", "kalshi", "opinion"}:
        try:
            orderbook = get_prediction_hunt_orderbook(
                platform=selected_market.platform,
                market_id=selected_market.marketId,
            )
        except PredictionHuntUpstreamError as exc:
            warnings.append(exc.detail)

    if effective_match_query:
        try:
            matching = get_prediction_hunt_matching_markets(q=effective_match_query)
        except PredictionHuntUpstreamError as exc:
            warnings.append(exc.detail)

    return PredictionHuntDeskSnapshotResponse(
        status=status,
        events=events,
        markets=markets,
        searchedMarkets=searched_markets,
        matching=matching,
        history=history,
        orderbook=orderbook,
        selectedMarket=selected_market,
        marketQuery=market_query,
        matchingQuery=effective_match_query,
        warnings=warnings,
        raw={},
    )


def _to_event_summary(raw: dict[str, Any]) -> PredictionHuntEventSummary:
    return PredictionHuntEventSummary(
        id=int(raw.get("id") or 0),
        eventName=str(raw.get("event_name") or "Untitled event"),
        eventType=str(raw.get("event_type") or "unknown"),
        eventDate=str(raw.get("event_date") or ""),
        status=str(raw.get("status") or "unknown"),
        groups=[
            PredictionHuntMatchGroupSummary(
                groupId=int(group.get("group_id") or 0),
                title=str(group.get("title") or "Untitled group"),
                platformCount=int(group.get("platform_count") or 0),
                platforms=[str(platform) for platform in group.get("platforms", [])],
            )
            for group in raw.get("groups", [])
        ],
    )


def _to_market_summary(raw: dict[str, Any]) -> PredictionHuntMarketSummary:
    price = raw.get("price") or {}
    return PredictionHuntMarketSummary(
        id=int(raw.get("id") or 0),
        marketId=str(raw.get("market_id") or ""),
        platform=str(raw.get("platform") or "unknown"),
        title=str(raw.get("title") or "Untitled market"),
        category=raw.get("category"),
        status=str(raw.get("status") or "unknown"),
        createdAt=raw.get("created_at") or raw.get("createdAt"),
        creationDate=raw.get("creation_date") or raw.get("creationDate"),
        expirationDate=raw.get("expiration_date"),
        sourceUrl=raw.get("source_url"),
        price=PredictionHuntPriceSnapshot(
            yesBid=_float_or_none(price.get("yes_bid")),
            yesAsk=_float_or_none(price.get("yes_ask")),
            noBid=_float_or_none(price.get("no_bid")),
            noAsk=_float_or_none(price.get("no_ask")),
            lastPrice=_float_or_none(price.get("last_price")),
            volume=_int_or_none(price.get("volume")),
            liquidity=_float_or_none(price.get("liquidity")),
        ),
    )


def _to_matching_event(raw: dict[str, Any]) -> PredictionHuntMatchingEvent:
    return PredictionHuntMatchingEvent(
        title=str(raw.get("title") or "Untitled event"),
        eventType=raw.get("event_type"),
        eventDate=raw.get("event_date"),
        confidence=raw.get("confidence"),
        groups=[
            PredictionHuntMatchingGroup(
                title=str(group.get("title") or "Untitled group"),
                markets=[
                    PredictionHuntMatchingMarket(
                        source=str(market.get("source") or "unknown"),
                        sourceUrl=market.get("source_url"),
                        id=str(market.get("id") or ""),
                    )
                    for market in group.get("markets", [])
                ],
            )
            for group in raw.get("groups", [])
        ],
    )


def _to_candle(raw: dict[str, Any]) -> PredictionHuntCandle:
    return PredictionHuntCandle(
        timestamp=str(raw.get("timestamp") or ""),
        open=_float_or_none(raw.get("open")),
        high=_float_or_none(raw.get("high")),
        low=_float_or_none(raw.get("low")),
        close=_float_or_none(raw.get("close")),
        yesBid=_float_or_none(raw.get("yes_bid")),
        yesAsk=_float_or_none(raw.get("yes_ask")),
        mid=_float_or_none(raw.get("mid")),
        volume=_int_or_none(raw.get("volume")),
        dollarVolume=_float_or_none(raw.get("dollar_volume")),
    )


def _to_orderbook_side(raw: dict[str, Any] | None) -> PredictionHuntOrderbookSide:
    raw = raw or {}
    return PredictionHuntOrderbookSide(
        bids=[_to_orderbook_level(item) for item in raw.get("bids", [])],
        asks=[_to_orderbook_level(item) for item in raw.get("asks", [])],
    )


def _to_orderbook_level(raw: dict[str, Any]) -> PredictionHuntOrderbookLevel:
    return PredictionHuntOrderbookLevel(
        price=float(raw.get("price") or 0),
        size=float(raw.get("size") or 0),
    )


def _to_platform_status(raw: dict[str, Any]) -> PredictionHuntPlatformStatus:
    return PredictionHuntPlatformStatus(
        status=str(raw.get("status") or "unknown"),
        lastUpdated=raw.get("last_updated"),
        activeMarkets=int(raw.get("active_markets") or 0),
    )


def _select_market(
    markets: list[PredictionHuntMarketSummary],
    *,
    market_id: str | None,
    platform: str | None,
) -> PredictionHuntMarketSummary | None:
    if market_id and platform:
        for market in markets:
            if market.marketId == market_id and market.platform == platform:
                return market
    return markets[0] if markets else None


def _extract_rate_limits(headers: requests.structures.CaseInsensitiveDict[str]) -> PredictionHuntRateLimitSnapshot:
    return PredictionHuntRateLimitSnapshot(
        perSecondLimit=_int_or_none(headers.get("X-RateLimit-Limit-Second")),
        perSecondRemaining=_int_or_none(headers.get("X-RateLimit-Remaining-Second")),
        perMonthLimit=_int_or_none(headers.get("X-RateLimit-Limit-Month")),
        perMonthRemaining=_int_or_none(headers.get("X-RateLimit-Remaining-Month")),
        retryAfterSeconds=_int_or_none(headers.get("Retry-After")),
    )


def _ttl_for_path(path: str) -> int:
    if path == "/status":
        return 60
    if path == "/matching-markets":
        return 60 * 60 * 6
    if path in {"/orderbook", "/prices/history"}:
        return 60 * 10
    return 60 * 5


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _build_upstream_detail(path: str, response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        payload = None

    if isinstance(payload, dict):
        message = payload.get("error") or payload.get("message")
        if message:
            return f"Prediction Hunt {path} returned {response.status_code}: {message}"
    return f"Prediction Hunt {path} returned {response.status_code}."


def _sorted_prediction_hunt_markets(
    markets: list[PredictionHuntMarketSummary],
) -> list[PredictionHuntMarketSummary]:
    return sorted(
        markets,
        key=lambda market: (
            market.platform.lower(),
            market.title.lower(),
            market.marketId.lower(),
        ),
    )


def _sorted_prediction_hunt_events(
    events: list[PredictionHuntEventSummary],
) -> list[PredictionHuntEventSummary]:
    normalized: list[PredictionHuntEventSummary] = []
    for event in events:
        normalized.append(
            event.model_copy(
                update={
                    "groups": sorted(
                        event.groups,
                        key=lambda group: (
                            group.title.lower(),
                            group.groupId,
                        ),
                    )
                }
            )
        )
    return sorted(
        normalized,
        key=lambda event: (
            event.eventDate,
            event.eventName.lower(),
            event.id,
        ),
    )


def _sorted_prediction_hunt_matching_events(
    events: list[PredictionHuntMatchingEvent],
) -> list[PredictionHuntMatchingEvent]:
    normalized: list[PredictionHuntMatchingEvent] = []
    for event in events:
        normalized_groups = []
        for group in event.groups:
            normalized_groups.append(
                group.model_copy(
                    update={
                        "markets": sorted(
                            group.markets,
                            key=lambda market: (
                                market.source.lower(),
                                market.id.lower(),
                            ),
                        )
                    }
                )
            )
        normalized.append(
            event.model_copy(
                update={
                    "groups": sorted(
                        normalized_groups,
                        key=lambda group: group.title.lower(),
                    )
                }
            )
        )
    return sorted(
        normalized,
        key=lambda event: (
            event.eventDate or "",
            event.title.lower(),
            event.confidence or "",
        ),
    )


@lru_cache(maxsize=1)
def _client() -> PredictionHuntClient:
    return PredictionHuntClient()
