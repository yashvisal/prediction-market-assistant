from fastapi import APIRouter, HTTPException, Query

from app.models.market import (
    DashboardSnapshotResponse,
    HealthResponse,
    MarketCategory,
    MarketDetail,
    MarketEventsResponse,
    MarketsResponse,
    MarketStatus,
)
from app.services.markets import (
    get_dashboard_snapshot,
    get_market_detail,
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
