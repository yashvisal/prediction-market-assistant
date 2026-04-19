from __future__ import annotations

import logging
from contextvars import ContextVar
from datetime import UTC, datetime

from app.data.mock_markets import get_market as get_mock_market
from app.data.mock_markets import get_market_events as get_mock_market_events
from app.data.mock_markets import list_markets as list_mock_markets
from app.models.market import (
    DashboardSnapshotResponse,
    Entity,
    EntityType,
    MarketCategory,
    MarketDetail,
    MarketEvent,
    MarketEventFeedItem,
    MarketStatus,
    MovementDirection,
    Signal,
    SignalSourceType,
)
from app.models.prediction_hunt import PredictionHuntCandle, PredictionHuntMarketSummary
from app.services.prediction_hunt import (
    PredictionHuntNotConfiguredError,
    PredictionHuntUpstreamError,
    clear_prediction_hunt_http_cache,
    get_prediction_hunt_markets,
    get_prediction_hunt_price_history,
)

LOGGER = logging.getLogger(__name__)
CORE_MARKETS_LIMIT = 60
DASHBOARD_MARKET_LIMIT = 12
DASHBOARD_EVENT_MARKET_LIMIT = 6
DEFAULT_TIMESTAMP = "1970-01-01T00:00:00Z"
MIN_EVENT_MOVEMENT = 0.01

# Request-local raw market cache used to avoid repeated /markets lookups.
_raw_markets_cache: ContextVar[dict[str, PredictionHuntMarketSummary] | None] = ContextVar(
    "prediction_hunt_raw_markets_cache",
    default=None,
)


def initialize_runtime() -> None:
    LOGGER.info("prediction_hunt_runtime_ready")


def list_market_summaries(
    *, status: MarketStatus | None = None, category: MarketCategory | None = None
) -> list[MarketDetail]:
    markets = _load_prediction_hunt_markets()
    if markets is None:
        LOGGER.warning(
            "prediction_hunt_core_fallback target=markets status=%s category=%s",
            status.value if status else "all",
            category.value if category else "all",
        )
        return list_mock_markets(status=status, category=category)

    return [
        market
        for market in markets
        if (status is None or market.status == status) and (category is None or market.category == category)
    ]


def get_market_detail(market_id: str) -> MarketDetail | None:
    markets = _load_prediction_hunt_markets()
    if markets is None:
        LOGGER.warning("prediction_hunt_core_fallback target=market_detail market_id=%s", market_id)
        return get_mock_market(market_id)

    return next((market for market in markets if market.id == market_id), None)


def list_market_events(
    market_id: str, *, market: MarketDetail | None = None, raw_market: PredictionHuntMarketSummary | None = None
) -> list[MarketEvent]:
    """Resolve events for a market. Pass ``market`` / ``raw_market`` when already loaded to avoid duplicate fetches."""
    if market is not None and raw_market is not None:
        return _safe_load_prediction_hunt_events(market=market, raw_market=raw_market, market_id=market_id)

    ph_list = _load_prediction_hunt_markets()
    if ph_list is None:
        if get_mock_market(market_id):
            return get_mock_market_events(market_id)
        return []

    detail = market if market is not None else next((m for m in ph_list if m.id == market_id), None)
    if detail is None:
        return []

    if raw_market is not None:
        return _safe_load_prediction_hunt_events(market=detail, raw_market=raw_market, market_id=market_id)

    resolved_raw = _find_prediction_hunt_market(market_id)
    if resolved_raw is None:
        LOGGER.warning("prediction_hunt_event_skip market_id=%s reason=market_not_in_core_set", market_id)
        return []
    return _safe_load_prediction_hunt_events(market=detail, raw_market=resolved_raw, market_id=market_id)


def get_dashboard_snapshot() -> DashboardSnapshotResponse:
    bundle = _fetch_prediction_hunt_markets_bundle()
    if bundle is None:
        LOGGER.warning(
            "prediction_hunt_core_fallback target=dashboard status=%s category=%s",
            MarketStatus.OPEN.value,
            "all",
        )
        markets = list_mock_markets(status=MarketStatus.OPEN)
        raw_by_id: dict[str, PredictionHuntMarketSummary] = {}
    else:
        detail_list, raw_by_id = bundle
        markets = [m for m in detail_list if m.status == MarketStatus.OPEN]

    active_markets = markets[:DASHBOARD_MARKET_LIMIT]

    top_events: list[MarketEventFeedItem] = []
    for market in active_markets[:DASHBOARD_EVENT_MARKET_LIMIT]:
        raw = raw_by_id.get(market.id)
        for event in list_market_events(market.id, market=market, raw_market=raw):
            top_events.append(
                MarketEventFeedItem(
                    **event.model_dump(),
                    marketTitle=market.title,
                    marketCategory=market.category,
                    marketStatus=market.status,
                )
            )

    top_events.sort(key=lambda item: abs(item.movementPercent), reverse=True)
    return DashboardSnapshotResponse(activeMarkets=active_markets, topEvents=top_events[:4])


def _fetch_prediction_hunt_markets_bundle() -> (
    tuple[list[MarketDetail], dict[str, PredictionHuntMarketSummary]] | None
):
    """Single upstream /markets fetch producing mapped details plus raw rows keyed by market id."""
    raw_by_id: dict[str, PredictionHuntMarketSummary] = {}
    _raw_markets_cache.set(raw_by_id)
    try:
        response = get_prediction_hunt_markets(limit=CORE_MARKETS_LIMIT, status="active")
    except PredictionHuntNotConfiguredError:
        clear_prediction_hunt_http_cache()
        _raw_markets_cache.set({})
        return None
    except PredictionHuntUpstreamError as exc:
        LOGGER.warning("prediction_hunt_market_load_failed detail=%s", exc.detail)
        clear_prediction_hunt_http_cache()
        _raw_markets_cache.set({})
        return None

    mapped: list[MarketDetail] = []
    for raw_market in response.markets:
        raw_by_id[raw_market.marketId] = raw_market
        try:
            mapped.append(_map_prediction_hunt_market(raw_market))
        except Exception:
            LOGGER.exception(
                "prediction_hunt_market_mapping_failed market_id=%s platform=%s",
                raw_market.marketId,
                raw_market.platform,
            )
    LOGGER.info("prediction_hunt_market_load_success count=%s", len(mapped))
    return mapped, raw_by_id


def _load_prediction_hunt_markets() -> list[MarketDetail] | None:
    bundle = _fetch_prediction_hunt_markets_bundle()
    return None if bundle is None else bundle[0]


def _find_prediction_hunt_market(market_id: str, raw_market: PredictionHuntMarketSummary | None = None) -> PredictionHuntMarketSummary | None:
    # If raw_market is provided, return it directly
    if raw_market is not None:
        return raw_market

    # Otherwise, check the cache
    cached_raw_markets = _raw_markets_cache.get()
    if cached_raw_markets is None:
        return None
    return cached_raw_markets.get(market_id)


def _safe_load_prediction_hunt_events(
    *,
    market: MarketDetail,
    raw_market: PredictionHuntMarketSummary,
    market_id: str,
) -> list[MarketEvent]:
    try:
        return _load_prediction_hunt_events_for_market(market=market, raw_market=raw_market)
    except (PredictionHuntNotConfiguredError, PredictionHuntUpstreamError) as exc:
        LOGGER.warning(
            "prediction_hunt_core_event_fallback market_id=%s reason=%s",
            market_id,
            str(exc),
        )
        return get_mock_market_events(market_id) if get_mock_market(market_id) else []


def _load_prediction_hunt_events_for_market(
    *,
    market: MarketDetail,
    raw_market: PredictionHuntMarketSummary,
) -> list[MarketEvent]:
    history = get_prediction_hunt_price_history(
        platform=raw_market.platform,
        market_id=market.id,
        interval="1h",
    )
    event = _build_recent_move_event(market=market, platform=raw_market.platform, candles=history.candles)
    return [event] if event else []


def _market_created_at(raw_market: PredictionHuntMarketSummary) -> str:
    if raw_market.createdAt:
        return raw_market.createdAt
    if raw_market.creationDate:
        return raw_market.creationDate

    # Prediction Hunt does not always expose a creation timestamp. When it is
    # missing, emit the current UTC time instead of incorrectly reusing expiry.
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _map_prediction_hunt_market(raw_market: PredictionHuntMarketSummary) -> MarketDetail:
    current_probability = _current_probability(raw_market)
    previous_close = _previous_close(raw_market, current_probability)
    category = _map_category(raw_market.category, raw_market.title)
    created_at = _market_created_at(raw_market)
    closes_at = raw_market.expirationDate or DEFAULT_TIMESTAMP
    status = _map_status(raw_market.status)
    description_bits = [
        f"Prediction Hunt market on platform={raw_market.platform}.",
        "This is the current plumbing-stage provider mapping.",
    ]
    if raw_market.category:
        description_bits.append(f"Provider category: {raw_market.category}.")
    if raw_market.sourceUrl:
        description_bits.append("Open the provider market for full source context.")

    return MarketDetail(
        id=raw_market.marketId,
        title=raw_market.title,
        description=" ".join(description_bits),
        status=status,
        category=category,
        currentProbability=current_probability,
        previousClose=previous_close,
        volume=(raw_market.price.volume or 0),
        liquidity=round(raw_market.price.liquidity or 0),
        createdAt=created_at,
        closesAt=closes_at,
        resolvedAt=closes_at if status == MarketStatus.RESOLVED else None,
        resolution=None,
        eventCount=0,
        lastEventAt=None,
    )


def _build_recent_move_event(
    *,
    market: MarketDetail,
    platform: str,
    candles: list[PredictionHuntCandle],
) -> MarketEvent | None:
    priced_candles = [(candle, _candle_probability(candle)) for candle in candles]
    usable = [(candle, probability) for candle, probability in priced_candles if probability is not None]
    if len(usable) < 2:
        LOGGER.info("prediction_hunt_event_skip market_id=%s reason=insufficient_history", market.id)
        return None

    start_candle, start_probability = usable[0]
    end_candle, end_probability = usable[-1]
    assert start_probability is not None
    assert end_probability is not None

    movement = round(abs(end_probability - start_probability), 4)
    if movement < MIN_EVENT_MOVEMENT:
        LOGGER.info(
            "prediction_hunt_event_skip market_id=%s reason=movement_below_threshold movement=%s",
            market.id,
            movement,
        )
        return None

    direction = MovementDirection.UP if end_probability >= start_probability else MovementDirection.DOWN
    summary = (
        "Synthetic recent-move event derived from Prediction Hunt price history during the plumbing stage."
    )
    return MarketEvent(
        id=f"{market.id}:recent-move",
        marketId=market.id,
        title="Recent market movement",
        startTime=start_candle.timestamp,
        endTime=end_candle.timestamp,
        probabilityBefore=start_probability,
        probabilityAfter=end_probability,
        movementPercent=movement,
        direction=direction,
        signals=_build_market_signals(market, platform),
        entities=[],
        relatedEvents=[],
        summary=summary,
    )


def _build_market_signals(market: MarketDetail, platform: str) -> list[Signal]:
    signal_id = f"{market.id}:provider-context"
    entity_id = f"{market.id}:platform"
    return [
        Signal(
            id=signal_id,
            title="Prediction Hunt provider context",
            source="Prediction Hunt",
            sourceType=SignalSourceType.ANALYSIS,
            url="#",
            publishedAt=datetime.now(UTC).isoformat(),
            snippet=(
                f"Minimal provider-backed context for {market.title}. "
                f"Platform={platform}, current probability={market.currentProbability:.0%}."
            ),
            relevanceScore=0.5,
            entities=[
                Entity(
                    id=entity_id,
                    name=platform.title(),
                    type=EntityType.ORGANIZATION,
                )
            ],
        )
    ]


def _map_status(status: str) -> MarketStatus:
    normalized = status.strip().lower()
    if normalized == "active":
        return MarketStatus.OPEN
    if normalized in {"resolved", "settled"}:
        return MarketStatus.RESOLVED
    return MarketStatus.CLOSED


def _map_category(raw_category: str | None, title: str) -> MarketCategory:
    normalized = f"{raw_category or ''} {title}".lower()
    if any(token in normalized for token in ("election", "president", "senate", "congress", "politic")):
        return MarketCategory.POLITICS
    if any(token in normalized for token in ("bitcoin", "crypto", "ethereum", "solana", "token")):
        return MarketCategory.CRYPTO
    if any(token in normalized for token in ("soccer", "nba", "nfl", "mlb", "sports", "cup", "championship")):
        return MarketCategory.SPORTS
    if any(token in normalized for token in ("climate", "weather", "temperature", "hurricane")):
        return MarketCategory.CLIMATE
    if any(token in normalized for token in ("war", "china", "russia", "ukraine", "israel", "gaza")):
        return MarketCategory.GEOPOLITICS
    if any(token in normalized for token in ("ai", "technology", "tech", "openai", "apple", "tesla")):
        return MarketCategory.TECHNOLOGY
    if any(token in normalized for token in ("science", "space", "nasa", "drug", "trial", "fda")):
        return MarketCategory.SCIENCE
    return MarketCategory.FINANCE


def _first_float_or(*values: float | None) -> float | None:
    for value in values:
        if value is not None:
            return value
    return None


def _current_probability(raw_market: PredictionHuntMarketSummary) -> float:
    candidate = _first_float_or(
        raw_market.price.lastPrice,
        raw_market.price.yesBid,
        raw_market.price.yesAsk,
        _midpoint(raw_market.price.yesBid, raw_market.price.yesAsk),
    )
    return _clamp_probability(candidate if candidate is not None else 0.0)


def _previous_close(raw_market: PredictionHuntMarketSummary, current_probability: float) -> float:
    candidate = _first_float_or(
        _midpoint(raw_market.price.yesBid, raw_market.price.yesAsk),
        raw_market.price.yesBid,
        raw_market.price.yesAsk,
        current_probability,
    )
    return _clamp_probability(candidate if candidate is not None else 0.0)


def _candle_probability(candle: PredictionHuntCandle) -> float | None:
    candidate = _first_float_or(candle.close, candle.mid, _midpoint(candle.yesBid, candle.yesAsk))
    return _clamp_probability(candidate) if candidate is not None else None


def _midpoint(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return (a + b) / 2


def _clamp_probability(value: float) -> float:
    return round(min(max(value, 0.0), 1.0), 4)