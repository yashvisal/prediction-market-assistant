from enum import StrEnum
from typing import Literal

from pydantic import BaseModel


class MarketStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    RESOLVED = "resolved"


class MarketCategory(StrEnum):
    FINANCE = "finance"
    POLITICS = "politics"
    TECHNOLOGY = "technology"
    CRYPTO = "crypto"
    CLIMATE = "climate"
    GEOPOLITICS = "geopolitics"
    SCIENCE = "science"
    SPORTS = "sports"


class SignalSourceType(StrEnum):
    NEWS = "news"
    TWEET = "tweet"
    OFFICIAL = "official"
    ANALYSIS = "analysis"


class EntityType(StrEnum):
    PERSON = "person"
    ORGANIZATION = "organization"
    TOPIC = "topic"
    LEGISLATION = "legislation"


class RelationshipType(StrEnum):
    SHARED_ENTITY = "shared_entity"
    SHARED_SOURCE = "shared_source"
    TIME_OVERLAP = "time_overlap"


class MovementDirection(StrEnum):
    UP = "up"
    DOWN = "down"


class Entity(BaseModel):
    id: str
    name: str
    type: EntityType


class Signal(BaseModel):
    id: str
    title: str
    source: str
    sourceType: SignalSourceType
    url: str
    publishedAt: str
    snippet: str
    relevanceScore: float
    entities: list[Entity]


class RelatedEvent(BaseModel):
    id: str
    marketId: str
    marketTitle: str
    eventTitle: str
    relationship: RelationshipType
    sharedEntities: list[str] | None = None


class MarketEvent(BaseModel):
    id: str
    marketId: str
    title: str
    startTime: str
    endTime: str
    probabilityBefore: float
    probabilityAfter: float
    movementPercent: float
    direction: MovementDirection
    signals: list[Signal]
    entities: list[Entity]
    relatedEvents: list[RelatedEvent]
    summary: str | None = None


class MarketSummary(BaseModel):
    id: str
    title: str
    status: MarketStatus
    category: MarketCategory
    currentProbability: float
    previousClose: float
    volume: int
    liquidity: int
    createdAt: str
    closesAt: str
    resolvedAt: str | None = None
    resolution: Literal["yes", "no"] | None = None
    eventCount: int
    lastEventAt: str | None = None


class MarketDetail(MarketSummary):
    description: str


class MarketsResponse(BaseModel):
    items: list[MarketSummary]


class MarketEventsResponse(BaseModel):
    items: list[MarketEvent]


class MarketEventFeedItem(MarketEvent):
    marketTitle: str
    marketCategory: MarketCategory
    marketStatus: MarketStatus


class DashboardSnapshotResponse(BaseModel):
    activeMarkets: list[MarketSummary]
    topEvents: list[MarketEventFeedItem]


class HealthResponse(BaseModel):
    status: Literal["ok"]
