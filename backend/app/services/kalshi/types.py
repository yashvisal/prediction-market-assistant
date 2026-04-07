from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypedDict

from app.models.market import MarketCategory, MarketStatus, MovementDirection


class KalshiMarket(TypedDict, total=False):
    ticker: str
    event_ticker: str
    title: str | None
    yes_sub_title: str
    no_sub_title: str
    created_time: str
    updated_time: str
    close_time: str
    status: str
    last_price_dollars: str | None
    previous_price_dollars: str | None
    yes_bid_dollars: str | None
    yes_ask_dollars: str | None
    yes_bid_size_fp: str | None
    yes_ask_size_fp: str | None
    volume_fp: str | None
    volume_24h_fp: str | None
    liquidity_dollars: str | None
    open_interest_fp: str | None
    result: str | None
    rules_primary: str
    rules_secondary: str
    settlement_ts: str | None


class KalshiCandlestick(TypedDict, total=False):
    end_period_ts: int
    yes_bid: dict[str, str | None]
    yes_ask: dict[str, str | None]
    price: dict[str, str | None]
    volume_fp: str | None
    volume: str | None
    open_interest_fp: str | None
    open_interest: str | None


@dataclass(frozen=True)
class NormalizedMarket:
    id: str
    provider: str
    provider_market_ticker: str
    provider_event_ticker: str
    title: str
    description: str
    status: MarketStatus
    category: MarketCategory
    current_probability: float
    previous_close: float
    volume: int
    liquidity: int
    created_at: str
    closes_at: str
    resolved_at: str | None
    resolution: str | None
    detail_url: str
    rules_primary: str
    rules_secondary: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizedHistoryPoint:
    market_id: str
    timestamp: str
    probability: float
    yes_bid: float | None
    yes_ask: float | None
    volume: int | None
    open_interest: int | None
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizedLiveUpdate:
    market_id: str
    timestamp: str
    probability: float
    direction: MovementDirection
    metadata: dict[str, Any] = field(default_factory=dict)
