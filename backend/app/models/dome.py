from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class DomeMarketSide(BaseModel):
    id: str
    label: str
    price: float | None = None


class DomeMarketSummary(BaseModel):
    marketSlug: str
    conditionId: str | None = None
    eventSlug: str | None = None
    title: str
    status: str
    startTime: str
    endTime: str
    volume1Week: float
    volumeTotal: float
    tags: list[str]
    description: str | None = None
    image: str | None = None
    sideA: DomeMarketSide
    sideB: DomeMarketSide


class DomeTradeRecord(BaseModel):
    tokenId: str
    tokenLabel: str
    side: str
    price: float
    sharesNormalized: float
    timestamp: str
    txHash: str
    user: str
    taker: str


class DomeOrderbookLevel(BaseModel):
    price: float
    size: float


class DomeOrderbookSummary(BaseModel):
    timestamp: str
    indexedAt: str
    bestBid: float | None = None
    bestAsk: float | None = None
    spread: float | None = None
    bidDepthLevels: int
    askDepthLevels: int
    topBids: list[DomeOrderbookLevel]
    topAsks: list[DomeOrderbookLevel]


class DomeMarketQualitySummary(BaseModel):
    hasPrices: bool
    hasRecentTrades: bool
    hasOrderbook: bool
    recentTradeCount: int
    totalRecentShares: float
    lastTradeAt: str | None = None
    bestBid: float | None = None
    bestAsk: float | None = None
    spread: float | None = None
    marketAgeHours: float


class DomePriceSamplePoint(BaseModel):
    label: str
    atTime: str
    sideAPrice: float | None = None
    sideBPrice: float | None = None


class DomeMarketSampleItem(BaseModel):
    market: DomeMarketSummary
    quality: DomeMarketQualitySummary


class DomeEventMarket(BaseModel):
    marketSlug: str
    title: str
    status: str
    volumeTotal: float


class DomeEventSummary(BaseModel):
    eventSlug: str
    title: str
    subtitle: str | None = None
    status: str
    startTime: str
    endTime: str
    volumeFiatAmount: float
    tags: list[str]
    marketCount: int
    markets: list[DomeEventMarket] = []


class DomeMarketCoverageSummary(BaseModel):
    sampleSize: int
    priceCoverageRatio: float
    tradeCoverageRatio: float
    orderbookCoverageRatio: float
    averageRecentTradeCount: float
    averageSpread: float | None = None


class DomeMarketListResponse(BaseModel):
    items: list[DomeMarketSummary]
    total: int
    hasMore: bool


class DomeEventListResponse(BaseModel):
    items: list[DomeEventSummary]
    total: int
    hasMore: bool


class DomeMarketDiscoveryResponse(BaseModel):
    items: list[DomeMarketSampleItem]
    coverage: DomeMarketCoverageSummary
    total: int
    hasMore: bool


class DomeMarketDetailResponse(BaseModel):
    market: DomeMarketSummary
    quality: DomeMarketQualitySummary
    priceHistory: list[DomePriceSamplePoint]
    recentTrades: list[DomeTradeRecord]
    orderbook: DomeOrderbookSummary | None = None
    raw: dict[str, Any]
