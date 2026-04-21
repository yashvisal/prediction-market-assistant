from __future__ import annotations

import hashlib
import threading
import time
from dataclasses import dataclass

from app.config import get_settings
from app.models.intelligence import MovementDirection
from app.models.market import MarketCategory, MarketDetail, MarketEvent, MarketStatus
from app.models.topic import TopicDetail, TopicMarket, TopicState, TopicSummary, TopicUpdate
from app.services.markets import list_market_activity


@dataclass(frozen=True)
class TopicSeed:
    id: str
    title: str
    description: str
    query: str
    category: MarketCategory
    tokens: tuple[str, ...]
    entity_names: tuple[str, ...] = ()


TOPIC_SEEDS: tuple[TopicSeed, ...] = (
    TopicSeed(
        id="fed-policy",
        title="Fed Policy Expectations",
        description="Tracks how markets are repricing the path of Federal Reserve policy and inflation-sensitive policy expectations.",
        query="fed policy expectations",
        category=MarketCategory.FINANCE,
        tokens=("fed", "fomc", "rate cut", "interest rates", "inflation", "cpi"),
        entity_names=("Federal Reserve", "FOMC", "Consumer Price Index"),
    ),
    TopicSeed(
        id="ai-regulation",
        title="AI Regulation",
        description="Tracks whether major regulatory or legislative developments are shifting expectations around AI governance.",
        query="ai regulation",
        category=MarketCategory.TECHNOLOGY,
        tokens=("ai", "artificial intelligence", "frontier model", "safety bill", "regulation"),
        entity_names=("AI Safety Regulation", "AI Accountability Act", "OpenAI"),
    ),
    TopicSeed(
        id="bitcoin-market",
        title="Bitcoin Market Structure",
        description="Tracks macro and institutional developments that are moving bitcoin-related markets.",
        query="bitcoin market structure",
        category=MarketCategory.CRYPTO,
        tokens=("bitcoin", "btc", "etf", "crypto"),
        entity_names=("Bitcoin", "Bitcoin ETFs", "BlackRock"),
    ),
    TopicSeed(
        id="spaceflight",
        title="Spaceflight Milestones",
        description="Tracks whether major aerospace milestones are shifting confidence in key space programs.",
        query="spaceflight milestones",
        category=MarketCategory.SCIENCE,
        tokens=("spacex", "starship", "orbital flight", "launch license"),
        entity_names=("Starship", "SpaceX", "FAA"),
    ),
    TopicSeed(
        id="global-health",
        title="Global Health Risk",
        description="Tracks outbreak, pandemic, and emergency-response developments that are materially shifting global health expectations.",
        query="global health risk",
        category=MarketCategory.SCIENCE,
        tokens=("who", "h5n1", "pheic", "public health emergency", "avian influenza"),
        entity_names=("World Health Organization", "H5N1 Avian Influenza"),
    ),
    TopicSeed(
        id="transatlantic-trade",
        title="US-EU Trade Tensions",
        description="Tracks whether trade friction or negotiation progress is changing expectations around transatlantic economic relations.",
        query="us eu trade tensions",
        category=MarketCategory.GEOPOLITICS,
        tokens=("trade agreement", "tariff", "eu", "european union", "auto imports"),
        entity_names=("US-EU Trade Relations", "European Commission", "U.S. Trade Representative"),
    ),
)

_TOPIC_STATE_CACHE: tuple[float, list[TopicState]] | None = None
_TOPIC_STATE_LOCK = threading.Lock()


def clear_topic_state_cache() -> None:
    global _TOPIC_STATE_CACHE
    with _TOPIC_STATE_LOCK:
        _TOPIC_STATE_CACHE = None


def list_topics() -> list[TopicSummary]:
    topic_state = _load_topic_state()
    return [TopicSummary.model_validate(topic.model_dump(exclude={"markets", "updates"})) for topic in topic_state]


def get_topic_detail(topic_id: str) -> TopicDetail | None:
    return next(
        (TopicDetail.model_validate(topic.model_dump()) for topic in _load_topic_state() if topic.id == topic_id),
        None,
    )


def list_topic_state() -> list[TopicState]:
    return _load_topic_state()


def _load_topic_state() -> list[TopicState]:
    global _TOPIC_STATE_CACHE
    settings = get_settings()
    now = time.time()

    cached = _TOPIC_STATE_CACHE
    if cached and cached[0] > now:
        return cached[1]

    with _TOPIC_STATE_LOCK:
        cached = _TOPIC_STATE_CACHE
        if cached and cached[0] > time.time():
            return cached[1]

        topic_state = _build_topic_state()
        _TOPIC_STATE_CACHE = (time.time() + settings.topic_state_cache_ttl_seconds, topic_state)
        return topic_state


def _build_topic_details() -> list[TopicDetail]:
    return [TopicDetail.model_validate(topic.model_dump()) for topic in _build_topic_state()]


def _build_topic_state() -> list[TopicState]:
    assignments: dict[str, list[tuple[MarketDetail, list[MarketEvent]]]] = {seed.id: [] for seed in TOPIC_SEEDS}
    for market, events in list_market_activity(status=MarketStatus.OPEN):
        matched_seed = _match_seed(market, events)
        if matched_seed is None:
            continue
        assignments[matched_seed.id].append((market, events))

    topics: list[TopicState] = []
    for seed in TOPIC_SEEDS:
        members = assignments[seed.id]
        if not members:
            continue
        topics.append(_build_topic_state_entry(seed, members))

    topics.sort(
        key=lambda topic: (
            topic.strongestMovementPercent,
            topic.latestUpdateAt or "",
            topic.marketCount,
        ),
        reverse=True,
    )
    return topics


def _match_seed(market: MarketDetail, events: list[MarketEvent]) -> TopicSeed | None:
    best_seed: TopicSeed | None = None
    best_score = 0
    searchable_text = _searchable_text(market, events)

    for seed in TOPIC_SEEDS:
        score = 0
        if market.category == seed.category:
            score += 1

        for token in seed.tokens:
            if token in searchable_text:
                score += 2

        for entity_name in seed.entity_names:
            if entity_name.lower() in searchable_text:
                score += 3

        if score > best_score:
            best_seed = seed
            best_score = score

    return best_seed if best_score >= 3 else None


def _searchable_text(market: MarketDetail, events: list[MarketEvent]) -> str:
    bits = [market.title, market.description, market.category.value]
    for event in events:
        bits.extend(
            [
                event.title,
                event.summary or "",
                " ".join(entity.name for entity in event.entities),
                " ".join(signal.title for signal in event.signals),
                " ".join(signal.source for signal in event.signals),
            ]
        )
    return " ".join(bits).lower()


def _build_topic_detail(
    seed: TopicSeed, members: list[tuple[MarketDetail, list[MarketEvent]]]
) -> TopicDetail:
    return TopicDetail.model_validate(_build_topic_state_entry(seed, members).model_dump())


def _build_topic_state_entry(
    seed: TopicSeed, members: list[tuple[MarketDetail, list[MarketEvent]]]
) -> TopicState:
    topic_markets = [_build_topic_market(market, events) for market, events in members]
    topic_markets.sort(
        key=lambda market: (abs(market.currentMovementPercent), market.eventCount, market.title),
        reverse=True,
    )

    updates = [
        _build_topic_update(market, event)
        for market, events in members
        for event in events
    ]
    updates.sort(key=lambda update: (update.endTime, abs(update.movementPercent)), reverse=True)

    signal_ids = {signal.id for update in updates for signal in update.signals}
    strongest_movement_amount, strongest_movement_direction = _strongest_topic_movement(
        topic_markets, updates
    )
    latest_update_at = updates[0].endTime if updates else _latest_market_activity(topic_markets)

    return TopicState(
        id=seed.id,
        title=seed.title,
        description=seed.description,
        category=seed.category,
        query=seed.query,
        stateVersion=_build_state_version(seed.id, topic_markets, updates),
        marketCount=len(topic_markets),
        updateCount=len(updates),
        signalCount=len(signal_ids),
        strongestMovementPercent=round(strongest_movement_amount, 4),
        strongestMovementDirection=strongest_movement_direction,
        latestUpdateAt=latest_update_at,
        markets=topic_markets,
        updates=updates,
    )


def _build_topic_market(market: MarketDetail, events: list[MarketEvent]) -> TopicMarket:
    delta = round(market.currentProbability - market.previousClose, 4)
    direction = MovementDirection.UP if delta >= 0 else MovementDirection.DOWN
    return TopicMarket(
        id=market.id,
        title=market.title,
        category=market.category,
        status=market.status,
        currentProbability=market.currentProbability,
        previousClose=market.previousClose,
        currentMovementPercent=delta,
        currentDirection=direction,
        eventCount=len(events),
        lastEventAt=_latest_event_at(events) or market.lastEventAt,
    )


def _build_topic_update(market: MarketDetail, event: MarketEvent) -> TopicUpdate:
    return TopicUpdate(
        id=event.id,
        marketId=market.id,
        marketTitle=market.title,
        marketCategory=market.category,
        marketStatus=market.status,
        title=event.title,
        startTime=event.startTime,
        endTime=event.endTime,
        movementPercent=event.movementPercent,
        direction=event.direction,
        summary=event.summary,
        signals=event.signals,
        entities=event.entities,
    )


def _strongest_topic_movement(
    topic_markets: list[TopicMarket], updates: list[TopicUpdate]
) -> tuple[float, MovementDirection]:
    strongest_amount = 0.0
    strongest_direction = MovementDirection.UP

    for update in updates:
        movement = abs(update.movementPercent)
        if movement > strongest_amount:
            strongest_amount = movement
            strongest_direction = update.direction

    for market in topic_markets:
        movement = abs(market.currentMovementPercent)
        if movement > strongest_amount:
            strongest_amount = movement
            strongest_direction = market.currentDirection

    return strongest_amount, strongest_direction


def _latest_event_at(events: list[MarketEvent]) -> str | None:
    if not events:
        return None
    return max(event.endTime for event in events)


def _latest_market_activity(markets: list[TopicMarket]) -> str | None:
    timestamps = [market.lastEventAt for market in markets if market.lastEventAt]
    return max(timestamps) if timestamps else None


def _build_state_version(topic_id: str, markets: list[TopicMarket], updates: list[TopicUpdate]) -> str:
    payload = "|".join(
        [
            topic_id,
            *[
                f"market:{market.id}:{market.status.value}:{market.currentProbability}:{market.currentMovementPercent}:{market.lastEventAt or ''}"
                for market in markets
            ],
            *[
                f"update:{update.id}:{update.endTime}:{update.movementPercent}"
                for update in updates
            ],
        ]
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
