import logging

from fastapi import APIRouter, HTTPException, Query

from app.models.prediction_hunt import (
    PredictionHuntDeskSnapshotResponse,
    PredictionHuntEventsResponse,
    PredictionHuntMarketsResponse,
    PredictionHuntMatchingMarketsResponse,
    PredictionHuntOrderbookResponse,
    PredictionHuntPriceHistoryResponse,
    PredictionHuntStatusResponse,
)
from app.models.market import (
    DashboardSnapshotResponse,
    HealthResponse,
    MarketCategory,
    MarketDetail,
    MarketEventsResponse,
    MarketsResponse,
    MarketStatus,
)
from app.services.prediction_hunt import (
    PredictionHuntNotConfiguredError,
    PredictionHuntUpstreamError,
    get_prediction_hunt_desk_snapshot,
    get_prediction_hunt_events,
    get_prediction_hunt_markets,
    get_prediction_hunt_matching_markets,
    get_prediction_hunt_orderbook,
    get_prediction_hunt_price_history,
    get_prediction_hunt_status,
)
from app.services.markets import (
    get_dashboard_snapshot,
    get_market_detail,
    list_market_events,
    list_market_summaries,
)

router = APIRouter(prefix="/api")
LOGGER = logging.getLogger(__name__)


def _enum_log_value(value: object) -> str:
    if value is None:
        return "all"
    raw = getattr(value, "value", value)
    return str(raw)


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/dashboard", response_model=DashboardSnapshotResponse)
def dashboard_snapshot() -> DashboardSnapshotResponse:
    LOGGER.info("core_dashboard_requested")
    return get_dashboard_snapshot()


@router.get("/markets", response_model=MarketsResponse)
def markets_index(
    status: MarketStatus | None = Query(default=None),
    category: MarketCategory | None = Query(default=None),
) -> MarketsResponse:
    LOGGER.info(
        "core_markets_requested status=%s category=%s",
        _enum_log_value(status),
        _enum_log_value(category),
    )
    markets = list_market_summaries(status=status, category=category)
    items = [market.model_dump(exclude={"description"}) for market in markets]
    return MarketsResponse.model_validate({"items": items})


@router.get("/markets/{market_id}", response_model=MarketDetail)
def market_detail(market_id: str) -> MarketDetail:
    LOGGER.info("core_market_detail_requested market_id=%s", market_id)
    market = get_market_detail(market_id)

    if market is None:
        raise HTTPException(status_code=404, detail="Market not found.")

    return market


@router.get("/markets/{market_id}/events", response_model=MarketEventsResponse)
def market_events(market_id: str) -> MarketEventsResponse:
    LOGGER.info("core_market_events_requested market_id=%s", market_id)
    market = get_market_detail(market_id)

    if market is None:
        raise HTTPException(status_code=404, detail="Market not found.")

    return MarketEventsResponse(items=list_market_events(market_id))


@router.get("/internal/providers/prediction-hunt/status", response_model=PredictionHuntStatusResponse)
def prediction_hunt_status() -> PredictionHuntStatusResponse:
    return get_prediction_hunt_status()


@router.get("/internal/providers/prediction-hunt/events", response_model=PredictionHuntEventsResponse)
def prediction_hunt_events(
    limit: int = Query(default=6, ge=1, le=20),
    status: str = Query(default="active"),
    event_type: str | None = Query(default=None),
    q: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
) -> PredictionHuntEventsResponse:
    try:
        return get_prediction_hunt_events(
            limit=limit,
            status=status,
            event_type=event_type,
            q=q,
            cursor=cursor,
        )
    except PredictionHuntNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except PredictionHuntUpstreamError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.get("/internal/providers/prediction-hunt/markets", response_model=PredictionHuntMarketsResponse)
def prediction_hunt_markets(
    limit: int = Query(default=8, ge=1, le=25),
    status: str = Query(default="active"),
    platform: str | None = Query(default=None),
    category: str | None = Query(default=None),
    q: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
) -> PredictionHuntMarketsResponse:
    try:
        return get_prediction_hunt_markets(
            limit=limit,
            status=status,
            platform=platform,
            category=category,
            q=q,
            cursor=cursor,
        )
    except PredictionHuntNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except PredictionHuntUpstreamError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.get(
    "/internal/providers/prediction-hunt/matching-markets",
    response_model=PredictionHuntMatchingMarketsResponse,
)
def prediction_hunt_matching_markets(
    q: str | None = Query(default=None),
    polymarket_key: str | None = Query(default=None),
) -> PredictionHuntMatchingMarketsResponse:
    try:
        return get_prediction_hunt_matching_markets(
            q=q,
            polymarket_key=polymarket_key,
        )
    except PredictionHuntNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except PredictionHuntUpstreamError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.get("/internal/providers/prediction-hunt/prices/history", response_model=PredictionHuntPriceHistoryResponse)
def prediction_hunt_price_history(
    platform: str = Query(...),
    market_id: str = Query(...),
    from_iso: str | None = Query(default=None, alias="from"),
    to_iso: str | None = Query(default=None, alias="to"),
    interval: str = Query(default="1h"),
) -> PredictionHuntPriceHistoryResponse:
    try:
        return get_prediction_hunt_price_history(
            platform=platform,
            market_id=market_id,
            from_iso=from_iso,
            to_iso=to_iso,
            interval=interval,
        )
    except PredictionHuntNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except PredictionHuntUpstreamError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.get("/internal/providers/prediction-hunt/orderbook", response_model=PredictionHuntOrderbookResponse)
def prediction_hunt_orderbook(
    platform: str = Query(...),
    market_id: str = Query(...),
) -> PredictionHuntOrderbookResponse:
    try:
        return get_prediction_hunt_orderbook(platform=platform, market_id=market_id)
    except PredictionHuntNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except PredictionHuntUpstreamError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.get("/internal/providers/prediction-hunt/desk", response_model=PredictionHuntDeskSnapshotResponse)
def prediction_hunt_desk(
    events_limit: int = Query(default=6, ge=1, le=20),
    markets_limit: int = Query(default=8, ge=1, le=25),
    events_status: str = Query(default="active"),
    markets_status: str = Query(default="active"),
    market_platform: str | None = Query(default=None),
    market_category: str | None = Query(default=None),
    market_query: str | None = Query(default=None),
    selected_market_id: str | None = Query(default=None),
    selected_market_platform: str | None = Query(default=None),
    match_query: str | None = Query(default=None),
    history_interval: str = Query(default="1h"),
) -> PredictionHuntDeskSnapshotResponse:
    try:
        return get_prediction_hunt_desk_snapshot(
            events_limit=events_limit,
            markets_limit=markets_limit,
            events_status=events_status,
            markets_status=markets_status,
            market_platform=market_platform,
            market_category=market_category,
            market_query=market_query,
            selected_market_id=selected_market_id,
            selected_market_platform=selected_market_platform,
            match_query=match_query,
            history_interval=history_interval,
        )
    except PredictionHuntNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except PredictionHuntUpstreamError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
