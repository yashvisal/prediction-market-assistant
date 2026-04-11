from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models.market import MarketCategory, MarketStatus, MovementDirection


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


@dataclass(frozen=True)
class ProviderSelectionInputs:
    volume: float
    liquidity: float
    non_zero_price_fields: int
    recent_trade_count: int = 0
    has_orderbook: bool = False
    spread: float | None = None
    title_quality: float = 0.0
    event_volume: float = 0.0
    event_market_count: int = 1
    history_coverage_ratio: float = 0.0


@dataclass(frozen=True)
class ProviderMarketBundle:
    raw_market: dict[str, Any]
    history_payload: dict[str, Any]
    history_source: str
    source_url: str | None = None
    raw_event: dict[str, Any] | None = None


@dataclass(frozen=True)
class MarketSeed:
    pool: str
    raw_market: dict[str, Any]
    raw_event: dict[str, Any] | None
    prefetch_inputs: ProviderSelectionInputs
