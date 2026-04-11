from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.models.market import MarketCategory, MarketStatus
from app.services.provider_types import NormalizedHistoryPoint, NormalizedMarket


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _to_int(value: Any) -> int:
    parsed = _to_float(value)
    if parsed is None:
        return 0
    return int(parsed)


def _iso_from_unix(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=UTC).isoformat().replace("+00:00", "Z")


def _market_category(title: str, description: str, tags: list[str]) -> MarketCategory:
    haystack = f"{title} {description} {' '.join(tags)}".lower()
    rules = [
        (MarketCategory.CRYPTO, ("bitcoin", "ethereum", "crypto", "solana")),
        (MarketCategory.FINANCE, ("fed", "rate", "inflation", "treasury", "cpi", "jobs report", "recession")),
        (MarketCategory.POLITICS, ("election", "president", "senate", "congress", "governor", "trump", "biden")),
        (MarketCategory.CLIMATE, ("climate", "storm", "hurricane", "temperature", "rainfall", "wildfire")),
        (MarketCategory.GEOPOLITICS, ("china", "russia", "ukraine", "nato", "ceasefire", "tariff", "iran", "israel")),
        (MarketCategory.SCIENCE, ("fda", "trial", "who", "pandemic", "vaccine", "space", "disease")),
        (MarketCategory.SPORTS, ("nba", "mlb", "nfl", "series", "game", "playoff", "goal", "wins", "kills", "map")),
        (MarketCategory.TECHNOLOGY, ("ai", "openai", "chip", "semiconductor", "tesla", "robot", "gpu")),
    ]
    for category, terms in rules:
        if any(term in haystack for term in terms):
            return category
    return MarketCategory.TECHNOLOGY


def _status(raw_market: dict[str, Any]) -> MarketStatus:
    status = str(raw_market.get("status") or "open").lower()
    winning_side = raw_market.get("winning_side")
    if status == "open":
        return MarketStatus.OPEN
    if winning_side:
        return MarketStatus.RESOLVED
    return MarketStatus.CLOSED


def _resolution(raw_market: dict[str, Any]) -> str | None:
    winning_side = raw_market.get("winning_side")
    if not winning_side:
        return None
    normalized = str(winning_side).strip().lower()
    if normalized in {"yes", "no"}:
        return normalized
    return None


def normalize_dome_market(
    raw_market: dict[str, Any],
    *,
    raw_event: dict[str, Any] | None = None,
    side_a_price: float | None = None,
    side_b_price: float | None = None,
    web_base_url: str = "https://polymarket.com",
) -> NormalizedMarket:
    market_title = str(raw_market.get("title") or "Untitled market")
    event_title = str(raw_event.get("title") or "").strip() if raw_event else ""
    combined_title = market_title
    if event_title and event_title.lower() not in market_title.lower():
        combined_title = f"{event_title} · {market_title}"

    raw_description = str(raw_market.get("description") or "").strip()
    event_subtitle = str(raw_event.get("subtitle") or "").strip() if raw_event else ""
    description_parts = [part for part in (raw_description, event_subtitle) if part]
    description = " ".join(description_parts) or combined_title
    tags = [str(tag) for tag in raw_market.get("tags", [])]
    category = _market_category(combined_title, description, tags)

    current_probability = side_a_price
    if current_probability is None and side_b_price is not None:
        current_probability = round(1 - side_b_price, 4)
    if current_probability is None:
        current_probability = 0.5

    detail_target = str(raw_market.get("event_slug") or raw_market.get("market_slug") or "")
    detail_url = f"{web_base_url}/event/{detail_target}" if detail_target else web_base_url
    rules_primary = raw_description or event_subtitle or f"Polymarket market for {combined_title}."
    rules_secondary = str(raw_market.get("resolution_source") or raw_event.get("settlement_sources") or "") if raw_event else str(raw_market.get("resolution_source") or "")

    return NormalizedMarket(
        id=str(raw_market.get("market_slug") or ""),
        provider="dome",
        provider_market_ticker=str(raw_market.get("market_slug") or ""),
        provider_event_ticker=str(raw_market.get("event_slug") or raw_market.get("market_slug") or ""),
        title=combined_title,
        description=description,
        status=_status(raw_market),
        category=category,
        current_probability=round(current_probability, 4),
        previous_close=round(current_probability, 4),
        volume=_to_int(raw_market.get("volume_total")),
        liquidity=_to_int(raw_market.get("volume_1_week") or raw_market.get("volume_total")),
        created_at=_iso_from_unix(int(raw_market.get("start_time", 0))),
        closes_at=_iso_from_unix(int(raw_market.get("end_time", 0))),
        resolved_at=_iso_from_unix(int(raw_market["completed_time"])) if raw_market.get("completed_time") else None,
        resolution=_resolution(raw_market),
        detail_url=detail_url,
        rules_primary=rules_primary,
        rules_secondary=rules_secondary,
        metadata={
            "condition_id": raw_market.get("condition_id"),
            "event_slug": raw_market.get("event_slug"),
            "event_title": event_title or None,
            "event_subtitle": event_subtitle or None,
            "tags": tags,
            "side_a": raw_market.get("side_a"),
            "side_b": raw_market.get("side_b"),
            "provider_status": raw_market.get("status"),
            "event_market_count": raw_event.get("market_count") if raw_event else None,
            "event_volume": raw_event.get("volume_fiat_amount") if raw_event else None,
        },
    )


def normalize_dome_candlesticks(
    market_id: str,
    raw_market: dict[str, Any],
    candlestick_payload: dict[str, Any],
    *,
    source: str,
) -> list[NormalizedHistoryPoint]:
    token_id = str(raw_market.get("side_a", {}).get("id") or "")
    entries = candlestick_payload.get("candlesticks", [])
    selected_series = _select_side_series(entries, token_id)
    points: list[NormalizedHistoryPoint] = []
    for candle in sorted(selected_series, key=lambda item: int(item.get("end_period_ts", 0))):
        probability = _extract_probability(candle)
        if probability is None:
            continue
        yes_bid = candle.get("yes_bid", {})
        yes_ask = candle.get("yes_ask", {})
        points.append(
            NormalizedHistoryPoint(
                market_id=market_id,
                timestamp=_iso_from_unix(int(candle.get("end_period_ts", 0))),
                probability=round(probability, 4),
                yes_bid=_to_float(yes_bid.get("close_dollars") or yes_bid.get("close")) if isinstance(yes_bid, dict) else None,
                yes_ask=_to_float(yes_ask.get("close_dollars") or yes_ask.get("close")) if isinstance(yes_ask, dict) else None,
                volume=_to_int(candle.get("volume") or candle.get("volume_fp")),
                open_interest=_to_int(candle.get("open_interest") or candle.get("open_interest_fp")),
                source=source,
                metadata={"provider": "dome"},
            )
        )
    return points


def normalize_sampled_price_history(
    market_id: str,
    price_samples: list[dict[str, Any]],
    *,
    source: str,
) -> list[NormalizedHistoryPoint]:
    points: list[NormalizedHistoryPoint] = []
    for sample in price_samples:
        probability = _to_float(sample.get("sideAPrice"))
        timestamp = sample.get("atTime")
        if probability is None or not timestamp:
            continue
        points.append(
            NormalizedHistoryPoint(
                market_id=market_id,
                timestamp=str(timestamp),
                probability=round(probability, 4),
                yes_bid=None,
                yes_ask=None,
                volume=None,
                open_interest=None,
                source=source,
                metadata={"label": sample.get("label")},
            )
        )
    return sorted(points, key=lambda item: item.timestamp)


def _select_side_series(entries: list[Any], token_id: str) -> list[dict[str, Any]]:
    if not entries:
        return []

    if isinstance(entries[0], dict):
        return [item for item in entries if isinstance(item, dict)]

    for entry in entries:
        if not isinstance(entry, list) or len(entry) != 2:
            continue
        series, metadata = entry
        if not isinstance(series, list) or not isinstance(metadata, dict):
            continue
        if str(metadata.get("token_id") or "") == token_id:
            return [item for item in series if isinstance(item, dict)]

    for entry in entries:
        if not isinstance(entry, list) or len(entry) != 2 or not isinstance(entry[0], list):
            continue
        return [item for item in entry[0] if isinstance(item, dict)]
    return []


def _extract_probability(candle: dict[str, Any]) -> float | None:
    price = candle.get("price", {})
    if isinstance(price, dict):
        for key in ("close_dollars", "close", "mean_dollars", "mean", "previous_dollars", "previous"):
            value = _to_float(price.get(key))
            if value is not None:
                return value

    yes_bid = candle.get("yes_bid", {})
    yes_ask = candle.get("yes_ask", {})
    bid_close = _to_float(yes_bid.get("close_dollars") or yes_bid.get("close")) if isinstance(yes_bid, dict) else None
    ask_close = _to_float(yes_ask.get("close_dollars") or yes_ask.get("close")) if isinstance(yes_ask, dict) else None
    if bid_close is not None and ask_close is not None:
        return round((bid_close + ask_close) / 2, 4)
    return bid_close or ask_close
