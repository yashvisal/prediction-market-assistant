from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

import requests

from app.models.dome import (
    DomeEventListResponse,
    DomeEventMarket,
    DomeEventSummary,
    DomeMarketCoverageSummary,
    DomeMarketDetailResponse,
    DomeMarketDiscoveryResponse,
    DomeMarketListResponse,
    DomeMarketQualitySummary,
    DomeMarketSampleItem,
    DomeMarketSide,
    DomeMarketSummary,
    DomeOrderbookLevel,
    DomeOrderbookSummary,
    DomePriceSamplePoint,
    DomeTradeRecord,
)
from app.services.dome_normalize import (
    normalize_dome_candlesticks,
    normalize_dome_market,
    normalize_sampled_price_history,
)
from app.services.provider_types import (
    MarketSeed,
    NormalizedHistoryPoint,
    NormalizedMarket,
    ProviderMarketBundle,
    ProviderSelectionInputs,
)


@dataclass(frozen=True)
class DomeHydratedMarket:
    bundle: ProviderMarketBundle
    normalized_market: NormalizedMarket
    history: list[NormalizedHistoryPoint]
    selection_inputs: ProviderSelectionInputs
    recent_trades: list[DomeTradeRecord]
    orderbook: DomeOrderbookSummary | None
    price_history: list[DomePriceSamplePoint]


class DomeNotConfiguredError(RuntimeError):
    pass


class DomeMarketNotFoundError(KeyError):
    pass


class DomeEventNotFoundError(KeyError):
    pass


_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


class DomeClient:
    def __init__(self) -> None:
        self._api_key = os.getenv("DOME_API_KEY")
        self._base_url = os.getenv("DOME_API_BASE_URL", "https://api.domeapi.io/v1").rstrip("/")
        if not self._api_key:
            raise DomeNotConfiguredError("Missing DOME_API_KEY.")
        self._session = requests.Session()

    def _get(self, path: str, *, params: dict[str, object] | None = None) -> dict[str, Any]:
        cache_key = json.dumps({"path": path, "params": params or {}}, sort_keys=True, default=str)
        now = time.time()
        cached = _CACHE.get(cache_key)
        if cached and cached[0] > now:
            return cached[1]

        try:
            response = self._session.get(
                f"{self._base_url}{path}",
                params=params,
                headers={"Authorization": f"Bearer {self._api_key}", "Accept": "application/json"},
                timeout=20,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            if _status_code(exc) == 429 and cached:
                return cached[1]
            raise

        payload = response.json()
        _CACHE[cache_key] = (now + _ttl_for_path(path), payload)
        return payload

    def list_markets(
        self,
        *,
        limit: int = 12,
        market_slug: str | None = None,
        status: str | None = None,
        min_volume: float | None = None,
    ) -> dict[str, Any]:
        params: dict[str, object] = {"limit": limit}
        if market_slug:
            params["market_slug"] = market_slug
        if status:
            params["status"] = status
        if min_volume is not None:
            params["min_volume"] = min_volume
        return self._get("/polymarket/markets", params=params)

    def list_events(
        self,
        *,
        limit: int = 8,
        status: str | None = None,
        include_markets: bool = False,
        event_slug: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, object] = {"limit": limit, "include_markets": "true" if include_markets else "false"}
        if status:
            params["status"] = status
        if event_slug:
            params["event_slug"] = event_slug
        return self._get("/polymarket/events", params=params)

    def get_market(self, market_slug: str) -> dict[str, Any]:
        payload = self.list_markets(limit=1, market_slug=market_slug)
        markets = payload.get("markets", [])
        if not markets:
            raise DomeMarketNotFoundError(market_slug)
        return markets[0]

    def get_event(self, event_slug: str) -> dict[str, Any]:
        payload = self.list_events(limit=1, event_slug=event_slug, include_markets=True)
        events = payload.get("events", [])
        if not events:
            raise DomeEventNotFoundError(event_slug)
        return events[0]

    def get_market_price(self, token_id: str) -> dict[str, Any]:
        return self._get(f"/polymarket/market-price/{token_id}")

    def get_historical_market_price(self, token_id: str, at_time: int) -> dict[str, Any]:
        try:
            return self._get(f"/polymarket/market-price/{token_id}", params={"at_time": at_time})
        except requests.HTTPError as exc:
            if _status_code(exc) == 404:
                return {"price": None, "at_time": at_time}
            raise

    def get_orders(self, *, market_slug: str, limit: int = 12) -> dict[str, Any]:
        return self._get("/polymarket/orders", params={"market_slug": market_slug, "limit": limit})

    def get_orderbook(self, *, token_id: str) -> dict[str, Any]:
        try:
            return self._get("/polymarket/orderbooks", params={"token_id": token_id})
        except requests.HTTPError as exc:
            if _status_code(exc) == 404:
                return {"snapshots": []}
            raise

    def get_candlesticks(
        self,
        *,
        condition_id: str,
        start_time: int,
        end_time: int,
        interval: int,
    ) -> dict[str, Any]:
        try:
            return self._get(
                f"/polymarket/candlesticks/{condition_id}",
                params={"start_time": start_time, "end_time": end_time, "interval": interval},
            )
        except requests.HTTPError as exc:
            if _status_code(exc) == 404:
                return {"candlesticks": []}
            raise


@lru_cache(maxsize=1)
def _client() -> DomeClient:
    return DomeClient()


def list_dome_polymarket_markets(limit: int = 12) -> DomeMarketListResponse:
    payload = _client().list_markets(limit=limit)
    pagination = payload.get("pagination", {})
    return DomeMarketListResponse(
        items=[_to_market_summary(item) for item in payload.get("markets", [])],
        total=int(pagination.get("total", 0)),
        hasMore=bool(pagination.get("has_more", False)),
    )


def list_dome_polymarket_events(limit: int = 8, status: str = "open") -> DomeEventListResponse:
    payload = _client().list_events(limit=limit, status=status, include_markets=True)
    pagination = payload.get("pagination", {})
    return DomeEventListResponse(
        items=[_to_event_summary(item) for item in payload.get("events", [])],
        total=int(pagination.get("total", 0)),
        hasMore=bool(pagination.get("has_more", False)),
    )


def sample_dome_polymarket_discovery(limit: int = 6) -> DomeMarketDiscoveryResponse:
    payload = _client().list_markets(limit=limit)
    pagination = payload.get("pagination", {})
    raw_markets = payload.get("markets", [])
    items = [_to_discovery_item(raw_market) for raw_market in raw_markets]

    spreads = [item.quality.spread for item in items if item.quality.spread is not None]
    sample_size = len(items)
    return DomeMarketDiscoveryResponse(
        items=items,
        coverage=DomeMarketCoverageSummary(
            sampleSize=sample_size,
            priceCoverageRatio=round(sum(1 for item in items if item.quality.hasPrices) / sample_size, 3)
            if sample_size
            else 0.0,
            tradeCoverageRatio=round(sum(1 for item in items if item.quality.hasRecentTrades) / sample_size, 3)
            if sample_size
            else 0.0,
            orderbookCoverageRatio=round(sum(1 for item in items if item.quality.hasOrderbook) / sample_size, 3)
            if sample_size
            else 0.0,
            averageRecentTradeCount=round(sum(item.quality.recentTradeCount for item in items) / sample_size, 2)
            if sample_size
            else 0.0,
            averageSpread=round(sum(spreads) / len(spreads), 4) if spreads else None,
        ),
        total=int(pagination.get("total", 0)),
        hasMore=bool(pagination.get("has_more", False)),
    )


def get_dome_polymarket_market(market_slug: str) -> DomeMarketDetailResponse:
    client = _client()
    raw_market = client.get_market(market_slug)
    raw_event = client.get_event(str(raw_market.get("event_slug"))) if raw_market.get("event_slug") else None
    hydrated = hydrate_dome_market(raw_market=raw_market, raw_event=raw_event, history_window_days=7)
    market = _to_market_summary(
        raw_market,
        side_a_price=hydrated.normalized_market.current_probability,
        side_b_price=_complementary_price(hydrated.normalized_market.current_probability),
    )

    return DomeMarketDetailResponse(
        market=market,
        quality=_build_quality_summary(market=market, recent_trades=hydrated.recent_trades, orderbook=hydrated.orderbook),
        priceHistory=hydrated.price_history,
        recentTrades=hydrated.recent_trades,
        orderbook=hydrated.orderbook,
        raw={
            "market": raw_market,
            "event": raw_event,
            "history": hydrated.bundle.history_payload,
            "price_history": [item.model_dump() for item in hydrated.price_history],
            "orderbook": hydrated.orderbook.model_dump() if hydrated.orderbook else None,
        },
    )


def list_dome_market_seeds(limit: int, *, status: str) -> list[MarketSeed]:
    events = _client().list_events(limit=limit, status=status, include_markets=True).get("events", [])
    pool = "open" if status == "open" else "historical"
    seeds: list[MarketSeed] = []
    for raw_event in events:
        for raw_market in raw_event.get("markets", []) or []:
            seeds.append(
                MarketSeed(
                    pool=pool,
                    raw_market=raw_market,
                    raw_event=raw_event,
                    prefetch_inputs=_build_prefetch_inputs(raw_market, raw_event),
                )
            )
    return seeds


def get_dome_market_seed(market_slug: str) -> MarketSeed:
    client = _client()
    raw_market = client.get_market(market_slug)
    raw_event = client.get_event(str(raw_market.get("event_slug"))) if raw_market.get("event_slug") else None
    pool = "open" if str(raw_market.get("status") or "open") == "open" else "historical"
    return MarketSeed(
        pool=pool,
        raw_market=raw_market,
        raw_event=raw_event,
        prefetch_inputs=_build_prefetch_inputs(raw_market, raw_event),
    )


def hydrate_dome_market(
    *,
    raw_market: dict[str, Any],
    raw_event: dict[str, Any] | None,
    history_window_days: int,
) -> DomeHydratedMarket:
    client = _client()
    raw_market = _ensure_full_market(client, raw_market)
    side_a_token_id = str(raw_market.get("side_a", {}).get("id") or "")
    side_b_token_id = str(raw_market.get("side_b", {}).get("id") or "")
    side_a_price = _safe_market_price(client, side_a_token_id)
    side_b_price = _safe_market_price(client, side_b_token_id)
    recent_trades = [_to_trade_record(item) for item in _safe_orders(client, market_slug=str(raw_market.get("market_slug")), limit=12).get("orders", [])]
    orderbook = _to_orderbook_summary(_safe_orderbook(client, token_id=side_a_token_id))
    normalized_market = normalize_dome_market(
        raw_market,
        raw_event=raw_event,
        side_a_price=side_a_price.get("price"),
        side_b_price=side_b_price.get("price"),
    )
    price_history = _sample_price_history(
        client=client,
        raw_market=raw_market,
        current_side_a_price=side_a_price,
        current_side_b_price=side_b_price,
    )
    history_payload, history_source = _load_history_payload(client, raw_market, history_window_days)
    history = normalize_dome_candlesticks(normalized_market.id, raw_market, history_payload, source=history_source)
    if len(history) < 2:
        history = normalize_sampled_price_history(
            normalized_market.id,
            [item.model_dump() for item in price_history],
            source="sampled_prices",
        )
        history_source = "sampled_prices"
        history_payload = {"points": [item.model_dump() for item in price_history]}

    if history:
        normalized_market = replace(
            normalized_market,
            previous_close=history[0].probability,
            current_probability=history[-1].probability if side_a_price.get("price") is None else normalized_market.current_probability,
            metadata={**normalized_market.metadata, "history_source": history_source},
        )

    selection_inputs = _build_selection_inputs(
        raw_market=raw_market,
        raw_event=raw_event,
        price_history=price_history,
        recent_trades=recent_trades,
        orderbook=orderbook,
        history=history,
        history_window_days=history_window_days,
        current_probability=normalized_market.current_probability,
    )
    return DomeHydratedMarket(
        bundle=ProviderMarketBundle(
            raw_market=raw_market,
            raw_event=raw_event,
            history_payload=history_payload,
            history_source=history_source,
            source_url=normalized_market.detail_url,
        ),
        normalized_market=normalized_market,
        history=history,
        selection_inputs=selection_inputs,
        recent_trades=recent_trades,
        orderbook=orderbook,
        price_history=price_history,
    )


def _ensure_full_market(client: DomeClient, raw_market: dict[str, Any]) -> dict[str, Any]:
    if raw_market.get("side_a", {}).get("id") and raw_market.get("condition_id"):
        return raw_market

    market_slug = str(raw_market.get("market_slug") or "")
    if not market_slug:
        return raw_market
    return client.get_market(market_slug)


def _to_market_summary(
    market: dict[str, Any],
    *,
    side_a_price: float | None = None,
    side_b_price: float | None = None,
) -> DomeMarketSummary:
    return DomeMarketSummary(
        marketSlug=str(market.get("market_slug", "")),
        conditionId=str(market.get("condition_id")) if market.get("condition_id") else None,
        eventSlug=market.get("event_slug"),
        title=str(market.get("title") or "Untitled market"),
        status=str(market.get("status") or "unknown"),
        startTime=_iso_from_unix_seconds(int(market.get("start_time", 0))),
        endTime=_iso_from_unix_seconds(int(market.get("end_time", 0))),
        volume1Week=float(market.get("volume_1_week") or 0),
        volumeTotal=float(market.get("volume_total") or 0),
        tags=[str(tag) for tag in market.get("tags", [])],
        description=market.get("description"),
        image=market.get("image"),
        sideA=DomeMarketSide(
            id=str(market.get("side_a", {}).get("id", "")),
            label=str(market.get("side_a", {}).get("label", "Yes")),
            price=side_a_price,
        ),
        sideB=DomeMarketSide(
            id=str(market.get("side_b", {}).get("id", "")),
            label=str(market.get("side_b", {}).get("label", "No")),
            price=side_b_price,
        ),
    )


def _to_event_summary(raw_event: dict[str, Any]) -> DomeEventSummary:
    return DomeEventSummary(
        eventSlug=str(raw_event.get("event_slug", "")),
        title=str(raw_event.get("title") or "Untitled event"),
        subtitle=raw_event.get("subtitle"),
        status=str(raw_event.get("status") or "unknown"),
        startTime=_iso_from_unix_seconds(int(raw_event.get("start_time", 0))),
        endTime=_iso_from_unix_seconds(int(raw_event.get("end_time", 0))),
        volumeFiatAmount=float(raw_event.get("volume_fiat_amount") or 0),
        tags=[str(tag) for tag in raw_event.get("tags", [])],
        marketCount=int(raw_event.get("market_count") or 0),
        markets=[
            DomeEventMarket(
                marketSlug=str(item.get("market_slug", "")),
                title=str(item.get("title") or "Untitled market"),
                status=str(item.get("status") or "unknown"),
                volumeTotal=float(item.get("volume_total") or 0),
            )
            for item in raw_event.get("markets", []) or []
        ],
    )


def _to_discovery_item(raw_market: dict[str, Any]) -> DomeMarketSampleItem:
    client = _client()
    side_a_price = _safe_market_price(client, str(raw_market.get("side_a", {}).get("id", "")))
    side_b_price = _safe_market_price(client, str(raw_market.get("side_b", {}).get("id", "")))
    raw_orders = _safe_orders(client, market_slug=str(raw_market.get("market_slug")), limit=6)
    raw_orderbook = _safe_orderbook(client, token_id=str(raw_market.get("side_a", {}).get("id", "")))
    market = _to_market_summary(raw_market, side_a_price=side_a_price.get("price"), side_b_price=side_b_price.get("price"))
    recent_trades = [_to_trade_record(item) for item in raw_orders.get("orders", [])]
    orderbook = _to_orderbook_summary(raw_orderbook)
    return DomeMarketSampleItem(
        market=market,
        quality=_build_quality_summary(market=market, recent_trades=recent_trades, orderbook=orderbook),
    )


def _to_trade_record(order: dict[str, Any]) -> DomeTradeRecord:
    return DomeTradeRecord(
        tokenId=str(order.get("token_id", "")),
        tokenLabel=str(order.get("token_label", "")),
        side=str(order.get("side", "")),
        price=float(order.get("price") or 0),
        sharesNormalized=float(order.get("shares_normalized") or 0),
        timestamp=_iso_from_unix_seconds(int(order.get("timestamp", 0))),
        txHash=str(order.get("tx_hash", "")),
        user=str(order.get("user", "")),
        taker=str(order.get("taker", "")),
    )


def _to_orderbook_summary(payload: dict[str, Any]) -> DomeOrderbookSummary | None:
    snapshots = payload.get("snapshots", [])
    if not snapshots:
        return None
    snapshot = snapshots[0]
    bids = [_to_orderbook_level(item) for item in snapshot.get("bids", [])]
    asks = [_to_orderbook_level(item) for item in snapshot.get("asks", [])]
    best_bid = bids[-1].price if bids else None
    best_ask = asks[0].price if asks else None
    spread = round(best_ask - best_bid, 4) if best_bid is not None and best_ask is not None else None
    top_bids = list(reversed(bids[-5:])) if bids else []
    top_asks = asks[:5]
    return DomeOrderbookSummary(
        timestamp=_iso_from_unix_milliseconds(int(snapshot.get("timestamp", 0))),
        indexedAt=_iso_from_unix_milliseconds(int(snapshot.get("indexedAt", 0))),
        bestBid=best_bid,
        bestAsk=best_ask,
        spread=spread,
        bidDepthLevels=len(bids),
        askDepthLevels=len(asks),
        topBids=top_bids,
        topAsks=top_asks,
    )


def _to_orderbook_level(level: dict[str, Any]) -> DomeOrderbookLevel:
    return DomeOrderbookLevel(price=float(level.get("price") or 0), size=float(level.get("size") or 0))


def _build_quality_summary(
    *,
    market: DomeMarketSummary,
    recent_trades: list[DomeTradeRecord],
    orderbook: DomeOrderbookSummary | None,
) -> DomeMarketQualitySummary:
    now = datetime.now(UTC)
    market_age_hours = round(
        max((now - datetime.fromisoformat(market.startTime.replace("Z", "+00:00"))).total_seconds(), 0) / 3600,
        2,
    )
    total_recent_shares = round(sum(item.sharesNormalized for item in recent_trades), 3)
    return DomeMarketQualitySummary(
        hasPrices=market.sideA.price is not None and market.sideB.price is not None,
        hasRecentTrades=bool(recent_trades),
        hasOrderbook=orderbook is not None,
        recentTradeCount=len(recent_trades),
        totalRecentShares=total_recent_shares,
        lastTradeAt=recent_trades[0].timestamp if recent_trades else None,
        bestBid=orderbook.bestBid if orderbook else None,
        bestAsk=orderbook.bestAsk if orderbook else None,
        spread=orderbook.spread if orderbook else None,
        marketAgeHours=market_age_hours,
    )


def _sample_price_history(
    *,
    client: DomeClient,
    raw_market: dict[str, Any],
    current_side_a_price: dict[str, Any] | None = None,
    current_side_b_price: dict[str, Any] | None = None,
) -> list[DomePriceSamplePoint]:
    now_ts = int(datetime.now(UTC).timestamp())
    market_start_ts = int(raw_market.get("start_time", now_ts))
    sample_offsets = [("now", 0), ("1h", 60 * 60), ("6h", 6 * 60 * 60), ("24h", 24 * 60 * 60)]
    points: list[DomePriceSamplePoint] = []
    seen_times: set[int] = set()
    for label, offset in sample_offsets:
        target_ts = max(market_start_ts, now_ts - offset)
        if target_ts in seen_times:
            continue
        seen_times.add(target_ts)
        side_a = current_side_a_price if offset == 0 and current_side_a_price is not None else _safe_historical_market_price(client, str(raw_market.get("side_a", {}).get("id", "")), target_ts)
        side_b = current_side_b_price if offset == 0 and current_side_b_price is not None else _safe_historical_market_price(client, str(raw_market.get("side_b", {}).get("id", "")), target_ts)
        at_time = int(side_a.get("at_time") or side_b.get("at_time") or target_ts)
        points.append(
            DomePriceSamplePoint(
                label=label,
                atTime=_iso_from_unix_seconds(at_time),
                sideAPrice=side_a.get("price"),
                sideBPrice=side_b.get("price"),
            )
        )
    return points


def _load_history_payload(client: DomeClient, raw_market: dict[str, Any], history_window_days: int) -> tuple[dict[str, Any], str]:
    condition_id = str(raw_market.get("condition_id") or "")
    if not condition_id:
        return {"candlesticks": []}, "missing_condition_id"

    now_ts = int(datetime.now(UTC).timestamp())
    start_ts = max(int(raw_market.get("start_time", now_ts)), now_ts - (history_window_days * 24 * 60 * 60))
    interval = 60 if history_window_days <= 31 else 1440
    payload = _safe_candlesticks(
        client,
        condition_id=condition_id,
        start_time=start_ts,
        end_time=now_ts,
        interval=interval,
    )
    return payload, f"dome_candlesticks_{interval}"


def _build_prefetch_inputs(raw_market: dict[str, Any], raw_event: dict[str, Any] | None) -> ProviderSelectionInputs:
    market_title = str(raw_market.get("title") or "")
    event_title = str(raw_event.get("title") or "") if raw_event else ""
    return ProviderSelectionInputs(
        volume=float(raw_market.get("volume_total") or 0),
        liquidity=float(raw_market.get("volume_1_week") or raw_market.get("volume_total") or 0),
        non_zero_price_fields=0,
        title_quality=_title_quality_score(market_title, event_title),
        event_volume=float(raw_event.get("volume_fiat_amount") or 0) if raw_event else 0.0,
        event_market_count=int(raw_event.get("market_count") or 1) if raw_event else 1,
        history_coverage_ratio=0.0,
    )


def _build_selection_inputs(
    *,
    raw_market: dict[str, Any],
    raw_event: dict[str, Any] | None,
    price_history: list[DomePriceSamplePoint],
    recent_trades: list[DomeTradeRecord],
    orderbook: DomeOrderbookSummary | None,
    history: list[NormalizedHistoryPoint],
    history_window_days: int,
    current_probability: float,
) -> ProviderSelectionInputs:
    non_zero_price_fields = 1 if current_probability > 0 else 0
    if orderbook and orderbook.bestBid is not None:
        non_zero_price_fields += 1
    if orderbook and orderbook.bestAsk is not None:
        non_zero_price_fields += 1
    non_zero_price_fields += sum(1 for point in price_history if point.sideAPrice not in (None, 0))
    expected_points = max(1, history_window_days * 24)
    market_title = str(raw_market.get("title") or "")
    event_title = str(raw_event.get("title") or "") if raw_event else ""
    return ProviderSelectionInputs(
        volume=float(raw_market.get("volume_total") or 0),
        liquidity=float(raw_market.get("volume_1_week") or raw_market.get("volume_total") or 0),
        non_zero_price_fields=min(non_zero_price_fields, 4),
        recent_trade_count=len(recent_trades),
        has_orderbook=orderbook is not None,
        spread=orderbook.spread if orderbook else None,
        title_quality=_title_quality_score(market_title, event_title),
        event_volume=float(raw_event.get("volume_fiat_amount") or 0) if raw_event else 0.0,
        event_market_count=int(raw_event.get("market_count") or 1) if raw_event else 1,
        history_coverage_ratio=min(len(history) / expected_points, 1.0),
    )


def _title_quality_score(market_title: str, event_title: str) -> float:
    combined = f"{event_title} {market_title}".strip()
    words = [part for part in combined.replace("?", "").split() if part]
    if not words:
        return 0.0
    score = min(len(words) / 12, 1.0)
    generic_terms = {"over/under", "winner", "total", "kills"}
    if any(term in market_title.lower() for term in generic_terms) and not event_title:
        score -= 0.25
    if "·" in combined or event_title:
        score += 0.15
    return round(max(0.0, min(score, 1.0)), 4)


def _safe_market_price(client: DomeClient, token_id: str) -> dict[str, Any]:
    try:
        return client.get_market_price(token_id)
    except requests.HTTPError as exc:
        if _status_code(exc) == 429:
            return {"price": None}
        raise


def _safe_historical_market_price(client: DomeClient, token_id: str, at_time: int) -> dict[str, Any]:
    try:
        return client.get_historical_market_price(token_id, at_time)
    except requests.HTTPError as exc:
        if _status_code(exc) == 429:
            return {"price": None, "at_time": at_time}
        raise


def _safe_orders(client: DomeClient, *, market_slug: str, limit: int) -> dict[str, Any]:
    try:
        return client.get_orders(market_slug=market_slug, limit=limit)
    except requests.HTTPError as exc:
        if _status_code(exc) == 429:
            return {"orders": []}
        raise


def _safe_orderbook(client: DomeClient, *, token_id: str) -> dict[str, Any]:
    try:
        return client.get_orderbook(token_id=token_id)
    except requests.HTTPError as exc:
        if _status_code(exc) == 429:
            return {"snapshots": []}
        raise


def _safe_candlesticks(
    client: DomeClient,
    *,
    condition_id: str,
    start_time: int,
    end_time: int,
    interval: int,
) -> dict[str, Any]:
    try:
        return client.get_candlesticks(
            condition_id=condition_id,
            start_time=start_time,
            end_time=end_time,
            interval=interval,
        )
    except requests.HTTPError as exc:
        if _status_code(exc) == 429:
            return {"candlesticks": []}
        raise


def _ttl_for_path(path: str) -> int:
    if "candlesticks" in path:
        return 300
    if "market-price" in path:
        return 30
    if "orderbooks" in path or "orders" in path:
        return 45
    if "events" in path or "markets" in path:
        return 120
    return 60


def _complementary_price(value: float | None) -> float | None:
    if value is None:
        return None
    return round(1 - value, 4)


def _status_code(exc: requests.HTTPError) -> int | None:
    return exc.response.status_code if exc.response is not None else None


def _iso_from_unix_seconds(value: int) -> str:
    return datetime.fromtimestamp(value, tz=UTC).isoformat().replace("+00:00", "Z")


def _iso_from_unix_milliseconds(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, tz=UTC).isoformat().replace("+00:00", "Z")
