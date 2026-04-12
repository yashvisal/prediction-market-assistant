from fastapi import APIRouter, HTTPException, Query

from app.models.dome import (
    DomeEventListResponse,
    DomeMarketDetailResponse,
    DomeMarketDiscoveryResponse,
    DomeMarketListResponse,
)
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
from app.models.evaluation import HeuristicEvaluationResponse, HeuristicMarketListResponse
from app.services.heuristics import HeuristicOverrides
from app.services.dome_markets import (
    DomeMarketNotFoundError,
    DomeNotConfiguredError,
    get_dome_polymarket_market,
    list_dome_polymarket_events,
    list_dome_polymarket_markets,
    sample_dome_polymarket_discovery,
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
    evaluate_market_heuristics,
    get_dashboard_snapshot,
    get_market_detail,
    list_heuristic_market_options,
    list_market_events,
    list_market_summaries,
)

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/dashboard", response_model=DashboardSnapshotResponse)
def dashboard_snapshot() -> DashboardSnapshotResponse:
    return get_dashboard_snapshot()


@router.get("/markets", response_model=MarketsResponse)
def markets_index(
    status: MarketStatus | None = Query(default=None),
    category: MarketCategory | None = Query(default=None),
) -> MarketsResponse:
    markets = list_market_summaries(status=status, category=category)
    items = [market.model_dump(exclude={"description"}) for market in markets]
    return MarketsResponse.model_validate({"items": items})


@router.get("/markets/{market_id}", response_model=MarketDetail)
def market_detail(market_id: str) -> MarketDetail:
    market = get_market_detail(market_id)

    if market is None:
        raise HTTPException(status_code=404, detail="Market not found.")

    return market


@router.get("/markets/{market_id}/events", response_model=MarketEventsResponse)
def market_events(market_id: str) -> MarketEventsResponse:
    market = get_market_detail(market_id)

    if market is None:
        raise HTTPException(status_code=404, detail="Market not found.")

    return MarketEventsResponse(items=list_market_events(market_id))


@router.get("/internal/heuristics/markets", response_model=HeuristicMarketListResponse)
def heuristic_markets() -> HeuristicMarketListResponse:
    return list_heuristic_market_options()


@router.get("/internal/dome/polymarket/markets", response_model=DomeMarketListResponse)
def dome_polymarket_markets(limit: int = Query(default=12, ge=1, le=24)) -> DomeMarketListResponse:
    try:
        return list_dome_polymarket_markets(limit=limit)
    except DomeNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/internal/dome/polymarket/discovery", response_model=DomeMarketDiscoveryResponse)
def dome_polymarket_discovery(limit: int = Query(default=6, ge=1, le=10)) -> DomeMarketDiscoveryResponse:
    try:
        return sample_dome_polymarket_discovery(limit=limit)
    except DomeNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/internal/dome/polymarket/events", response_model=DomeEventListResponse)
def dome_polymarket_events(
    limit: int = Query(default=8, ge=1, le=20),
    status: str = Query(default="open"),
) -> DomeEventListResponse:
    try:
        return list_dome_polymarket_events(limit=limit, status=status)
    except DomeNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/internal/dome/polymarket/markets/{market_slug:path}", response_model=DomeMarketDetailResponse)
def dome_polymarket_market_detail(market_slug: str) -> DomeMarketDetailResponse:
    try:
        return get_dome_polymarket_market(market_slug)
    except DomeNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except DomeMarketNotFoundError:
        raise HTTPException(status_code=404, detail="Market not found.")


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
    kalshi_key: str | None = Query(default=None),
) -> PredictionHuntMatchingMarketsResponse:
    try:
        return get_prediction_hunt_matching_markets(
            q=q,
            polymarket_key=polymarket_key,
            kalshi_key=kalshi_key,
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


@router.get(
    "/internal/heuristics/markets/{market_id}/evaluate",
    response_model=HeuristicEvaluationResponse,
)
def evaluate_market(
    market_id: str,
    tracked_market_limit: int | None = Query(default=None),
    historical_market_limit: int | None = Query(default=None),
    history_window_days: int | None = Query(default=None),
    event_threshold: float | None = Query(default=None),
    event_cooldown_points: int | None = Query(default=None),
    max_events_per_market: int | None = Query(default=None),
    max_signals_per_event: int | None = Query(default=None),
    routing_skip_below: float | None = Query(default=None),
    routing_deep_at_or_above: float | None = Query(default=None),
    scoring_base_rules: float | None = Query(default=None),
    scoring_base_snapshot: float | None = Query(default=None),
    scoring_bonus_1h: float | None = Query(default=None),
    scoring_bonus_6h: float | None = Query(default=None),
    scoring_bonus_24h: float | None = Query(default=None),
    selection_recent_movement_weight: float | None = Query(default=None),
    selection_non_zero_ratio_weight: float | None = Query(default=None),
    selection_volume_weight: float | None = Query(default=None),
    selection_open_interest_weight: float | None = Query(default=None),
    selection_history_weight: float | None = Query(default=None),
    selection_recent_trade_weight: float | None = Query(default=None),
    selection_orderbook_weight: float | None = Query(default=None),
    selection_event_volume_weight: float | None = Query(default=None),
    selection_title_quality_weight: float | None = Query(default=None),
    selection_spread_penalty: float | None = Query(default=None),
    selection_zero_price_penalty: float | None = Query(default=None),
    selection_candidate_pool_multiplier: int | None = Query(default=None),
    selection_min_points: int | None = Query(default=None),
    selection_min_non_zero_ratio: float | None = Query(default=None),
    selection_min_recent_trades: int | None = Query(default=None),
    selection_min_history_coverage: float | None = Query(default=None),
) -> HeuristicEvaluationResponse:
    overrides = HeuristicOverrides(
        tracked_market_limit=tracked_market_limit,
        historical_market_limit=historical_market_limit,
        history_window_days=history_window_days,
        event_threshold=event_threshold,
        event_cooldown_points=event_cooldown_points,
        max_events_per_market=max_events_per_market,
        max_signals_per_event=max_signals_per_event,
        routing_skip_below=routing_skip_below,
        routing_deep_at_or_above=routing_deep_at_or_above,
        scoring_base_rules=scoring_base_rules,
        scoring_base_snapshot=scoring_base_snapshot,
        scoring_bonus_1h=scoring_bonus_1h,
        scoring_bonus_6h=scoring_bonus_6h,
        scoring_bonus_24h=scoring_bonus_24h,
        selection_recent_movement_weight=selection_recent_movement_weight,
        selection_non_zero_ratio_weight=selection_non_zero_ratio_weight,
        selection_volume_weight=selection_volume_weight,
        selection_open_interest_weight=selection_open_interest_weight,
        selection_history_weight=selection_history_weight,
        selection_recent_trade_weight=selection_recent_trade_weight,
        selection_orderbook_weight=selection_orderbook_weight,
        selection_event_volume_weight=selection_event_volume_weight,
        selection_title_quality_weight=selection_title_quality_weight,
        selection_spread_penalty=selection_spread_penalty,
        selection_zero_price_penalty=selection_zero_price_penalty,
        selection_candidate_pool_multiplier=selection_candidate_pool_multiplier,
        selection_min_points=selection_min_points,
        selection_min_non_zero_ratio=selection_min_non_zero_ratio,
        selection_min_recent_trades=selection_min_recent_trades,
        selection_min_history_coverage=selection_min_history_coverage,
    )
    try:
        return evaluate_market_heuristics(market_id, overrides)
    except KeyError:
        raise HTTPException(status_code=404, detail="Market not found.")
