from app.data.mock_markets import get_market_events, get_market, list_markets
from app.models.market import (
    DashboardSnapshotResponse,
    MarketCategory,
    MarketDetail,
    MarketEventFeedItem,
    MarketStatus,
)


def list_market_summaries(
    *, status: MarketStatus | None = None, category: MarketCategory | None = None
):
    return list_markets(status=status, category=category)


def get_market_detail(market_id: str) -> MarketDetail | None:
    return get_market(market_id)


def list_market_events(market_id: str):
    return get_market_events(market_id)


def get_dashboard_snapshot() -> DashboardSnapshotResponse:
    markets = list_market_summaries()
    top_events = sorted(
        [
            MarketEventFeedItem(
                **event.model_dump(),
                marketTitle=market.title,
                marketCategory=market.category,
                marketStatus=market.status,
            )
            for market in markets
            for event in list_market_events(market.id)
        ],
        key=lambda event: abs(event.movementPercent),
        reverse=True,
    )[:4]

    return DashboardSnapshotResponse(
        activeMarkets=[market for market in markets if market.status == MarketStatus.OPEN],
        topEvents=top_events,
    )
