from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.models.market import MarketCategory, MarketStatus, MovementDirection
from app.services.kalshi.types import (
    KalshiCandlestick,
    KalshiMarket,
    NormalizedHistoryPoint,
    NormalizedLiveUpdate,
    NormalizedMarket,
)


STATUS_MAP = {
    "initialized": MarketStatus.OPEN,
    "inactive": MarketStatus.OPEN,
    "active": MarketStatus.OPEN,
    "closed": MarketStatus.CLOSED,
    "determined": MarketStatus.RESOLVED,
    "disputed": MarketStatus.RESOLVED,
    "amended": MarketStatus.RESOLVED,
    "finalized": MarketStatus.RESOLVED,
}


def _to_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _to_int(value: str | None) -> int:
    if value is None or value == "":
        return 0
    return int(float(value))


def _iso_from_unix(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=UTC).isoformat().replace("+00:00", "Z")


def _market_probability(raw_market: KalshiMarket) -> float:
    last_price = _to_float(raw_market.get("last_price_dollars"))
    if last_price is not None:
        return last_price

    yes_bid = _to_float(raw_market.get("yes_bid_dollars"))
    yes_ask = _to_float(raw_market.get("yes_ask_dollars"))
    if yes_bid is not None and yes_ask is not None:
        return round((yes_bid + yes_ask) / 2, 4)
    if yes_bid is not None:
        return yes_bid
    if yes_ask is not None:
        return yes_ask
    return 0.5


def _previous_close(raw_market: KalshiMarket) -> float:
    previous_price = _to_float(raw_market.get("previous_price_dollars"))
    if previous_price is not None:
        return previous_price
    return _market_probability(raw_market)


def _market_category(title: str, description: str) -> MarketCategory:
    haystack = f"{title} {description}".lower()
    rules = [
        (MarketCategory.CRYPTO, ("bitcoin", "ethereum", "crypto", "solana")),
        (MarketCategory.FINANCE, ("fed", "rate", "inflation", "treasury", "cpi", "jobs report", "recession")),
        (MarketCategory.POLITICS, ("election", "president", "senate", "congress", "governor", "trump", "biden")),
        (MarketCategory.CLIMATE, ("climate", "storm", "hurricane", "temperature", "rainfall", "wildfire")),
        (MarketCategory.GEOPOLITICS, ("china", "russia", "ukraine", "nato", "ceasefire", "tariff")),
        (MarketCategory.SCIENCE, ("fda", "trial", "who", "pandemic", "vaccine", "space", "disease")),
        (MarketCategory.SPORTS, ("nba", "mlb", "nfl", "series", "game", "playoff", "goal", "wins")),
        (MarketCategory.TECHNOLOGY, ("ai", "openai", "chip", "semiconductor", "tesla", "robot", "gpu")),
    ]
    for category, terms in rules:
        if any(term in haystack for term in terms):
            return category
    return MarketCategory.TECHNOLOGY


def normalize_market(raw_market: KalshiMarket, *, web_base_url: str) -> NormalizedMarket:
    title = raw_market.get("title") or raw_market.get("yes_sub_title") or raw_market["ticker"]
    description_parts = [raw_market.get("rules_primary"), raw_market.get("rules_secondary")]
    description = " ".join(part.strip() for part in description_parts if part and part.strip())
    category = _market_category(title, description)
    status = STATUS_MAP.get(raw_market.get("status", ""), MarketStatus.OPEN)
    resolution = raw_market.get("result") if raw_market.get("result") in {"yes", "no"} else None
    liquidity = _to_int(raw_market.get("open_interest_fp")) or _to_int(raw_market.get("volume_24h_fp"))
    return NormalizedMarket(
        id=raw_market["ticker"],
        provider="kalshi",
        provider_market_ticker=raw_market["ticker"],
        provider_event_ticker=raw_market.get("event_ticker", ""),
        title=title,
        description=description or f"Kalshi market for {title}.",
        status=status,
        category=category,
        current_probability=_market_probability(raw_market),
        previous_close=_previous_close(raw_market),
        volume=_to_int(raw_market.get("volume_fp")),
        liquidity=liquidity,
        created_at=raw_market["created_time"],
        closes_at=raw_market["close_time"],
        resolved_at=raw_market.get("settlement_ts"),
        resolution=resolution,
        detail_url=f"{web_base_url}/markets/{raw_market['ticker']}",
        rules_primary=raw_market.get("rules_primary", ""),
        rules_secondary=raw_market.get("rules_secondary", ""),
        metadata={
            "provider_status": raw_market.get("status"),
            "yes_bid_size_fp": raw_market.get("yes_bid_size_fp"),
            "yes_ask_size_fp": raw_market.get("yes_ask_size_fp"),
        },
    )


def normalize_candlesticks(
    market_id: str,
    candlesticks: list[KalshiCandlestick],
    *,
    source: str,
) -> list[NormalizedHistoryPoint]:
    points: list[NormalizedHistoryPoint] = []
    for candle in sorted(candlesticks, key=lambda item: item["end_period_ts"]):
        price = candle.get("price", {})
        probability = _to_float(price.get("close_dollars") or price.get("close") or price.get("previous_dollars") or price.get("previous"))
        if probability is None:
            yes_bid = candle.get("yes_bid", {})
            yes_ask = candle.get("yes_ask", {})
            yes_bid_close = _to_float(yes_bid.get("close_dollars") or yes_bid.get("close"))
            yes_ask_close = _to_float(yes_ask.get("close_dollars") or yes_ask.get("close"))
            if yes_bid_close is not None and yes_ask_close is not None:
                probability = round((yes_bid_close + yes_ask_close) / 2, 4)
            else:
                probability = yes_bid_close or yes_ask_close

        if probability is None:
            continue

        yes_bid = candle.get("yes_bid", {})
        yes_ask = candle.get("yes_ask", {})
        points.append(
            NormalizedHistoryPoint(
                market_id=market_id,
                timestamp=_iso_from_unix(candle["end_period_ts"]),
                probability=probability,
                yes_bid=_to_float(yes_bid.get("close_dollars") or yes_bid.get("close")),
                yes_ask=_to_float(yes_ask.get("close_dollars") or yes_ask.get("close")),
                volume=_to_int(candle.get("volume_fp") or candle.get("volume")),
                open_interest=_to_int(candle.get("open_interest_fp") or candle.get("open_interest")),
                source=source,
                metadata={},
            )
        )
    return points


def normalize_live_update(raw_message: dict[str, Any]) -> NormalizedLiveUpdate | None:
    ticker = raw_message.get("market_ticker") or raw_message.get("ticker")
    probability = raw_message.get("price")
    timestamp = raw_message.get("ts")
    if ticker is None or probability is None or timestamp is None:
        return None
    movement = raw_message.get("delta", 0)
    direction = MovementDirection.UP if movement >= 0 else MovementDirection.DOWN
    timestamp_iso = (
        _iso_from_unix(int(timestamp))
        if isinstance(timestamp, (int, float))
        else str(timestamp)
    )
    return NormalizedLiveUpdate(
        market_id=str(ticker),
        timestamp=timestamp_iso,
        probability=float(probability),
        direction=direction,
        metadata={k: v for k, v in raw_message.items() if k not in {"market_ticker", "ticker", "price", "ts"}},
    )
