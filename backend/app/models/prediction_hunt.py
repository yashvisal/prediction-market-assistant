from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class PredictionHuntRateLimitSnapshot(BaseModel):
    perSecondLimit: int | None = None
    perSecondRemaining: int | None = None
    perMonthLimit: int | None = None
    perMonthRemaining: int | None = None
    retryAfterSeconds: int | None = None


class PredictionHuntMatchGroupSummary(BaseModel):
    groupId: int
    title: str
    platformCount: int
    platforms: list[str]


class PredictionHuntEventSummary(BaseModel):
    id: int
    eventName: str
    eventType: str
    eventDate: str
    status: str
    groups: list[PredictionHuntMatchGroupSummary]


class PredictionHuntEventsResponse(BaseModel):
    events: list[PredictionHuntEventSummary]
    nextCursor: str | None = None
    totalCount: int
    rateLimits: PredictionHuntRateLimitSnapshot | None = None


class PredictionHuntPriceSnapshot(BaseModel):
    yesBid: float | None = None
    yesAsk: float | None = None
    noBid: float | None = None
    noAsk: float | None = None
    lastPrice: float | None = None
    volume: int | None = None
    liquidity: float | None = None


class PredictionHuntMarketSummary(BaseModel):
    id: int
    marketId: str
    platform: str
    title: str
    category: str | None = None
    status: str
    expirationDate: str | None = None
    sourceUrl: str | None = None
    price: PredictionHuntPriceSnapshot


class PredictionHuntMarketsResponse(BaseModel):
    markets: list[PredictionHuntMarketSummary]
    nextCursor: str | None = None
    totalCount: int
    rateLimits: PredictionHuntRateLimitSnapshot | None = None


class PredictionHuntMatchingMarket(BaseModel):
    source: str
    sourceUrl: str | None = None
    id: str


class PredictionHuntMatchingGroup(BaseModel):
    title: str
    markets: list[PredictionHuntMatchingMarket]


class PredictionHuntMatchingEvent(BaseModel):
    title: str
    eventType: str | None = None
    eventDate: str | None = None
    confidence: str | None = None
    groups: list[PredictionHuntMatchingGroup]


class PredictionHuntMatchingMarketsResponse(BaseModel):
    success: bool
    count: int
    events: list[PredictionHuntMatchingEvent]
    rateLimits: PredictionHuntRateLimitSnapshot | None = None


class PredictionHuntCandle(BaseModel):
    timestamp: str
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    yesBid: float | None = None
    yesAsk: float | None = None
    mid: float | None = None
    volume: int | None = None
    dollarVolume: float | None = None


class PredictionHuntPriceHistoryResponse(BaseModel):
    marketId: str
    platform: str
    interval: str
    candles: list[PredictionHuntCandle]
    rateLimits: PredictionHuntRateLimitSnapshot | None = None


class PredictionHuntOrderbookLevel(BaseModel):
    price: float
    size: float


class PredictionHuntOrderbookSide(BaseModel):
    bids: list[PredictionHuntOrderbookLevel]
    asks: list[PredictionHuntOrderbookLevel]


class PredictionHuntOrderbookResponse(BaseModel):
    marketId: str
    platform: str
    timestamp: str | None = None
    yes: PredictionHuntOrderbookSide
    no: PredictionHuntOrderbookSide
    rateLimits: PredictionHuntRateLimitSnapshot | None = None


class PredictionHuntPlatformStatus(BaseModel):
    status: str
    lastUpdated: str | None = None
    activeMarkets: int


class PredictionHuntStatusResponse(BaseModel):
    status: str
    platforms: dict[str, PredictionHuntPlatformStatus]
    rateLimits: PredictionHuntRateLimitSnapshot | None = None


class PredictionHuntDeskSnapshotResponse(BaseModel):
    status: PredictionHuntStatusResponse
    events: PredictionHuntEventsResponse
    markets: PredictionHuntMarketsResponse
    searchedMarkets: PredictionHuntMarketsResponse | None = None
    matching: PredictionHuntMatchingMarketsResponse | None = None
    history: PredictionHuntPriceHistoryResponse | None = None
    orderbook: PredictionHuntOrderbookResponse | None = None
    selectedMarket: PredictionHuntMarketSummary | None = None
    marketQuery: str | None = None
    matchingQuery: str | None = None
    warnings: list[str] = []
    raw: dict[str, Any] = {}
