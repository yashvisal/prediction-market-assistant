from __future__ import annotations

from typing import Any, TypedDict

from app.services.provider_types import NormalizedHistoryPoint, NormalizedLiveUpdate, NormalizedMarket


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
