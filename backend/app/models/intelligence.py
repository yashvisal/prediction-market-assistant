from enum import StrEnum

from pydantic import BaseModel


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
