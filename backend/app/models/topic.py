from __future__ import annotations

from pydantic import BaseModel

from app.models.intelligence import Entity, MovementDirection, Signal
from app.models.market import MarketCategory, MarketStatus


class TopicMarket(BaseModel):
    id: str
    title: str
    category: MarketCategory
    status: MarketStatus
    currentProbability: float
    previousClose: float
    currentMovementPercent: float
    currentDirection: MovementDirection
    eventCount: int
    lastEventAt: str | None = None


class TopicUpdate(BaseModel):
    id: str
    marketId: str
    marketTitle: str
    marketCategory: MarketCategory
    marketStatus: MarketStatus
    title: str
    startTime: str
    endTime: str
    movementPercent: float
    direction: MovementDirection
    summary: str | None = None
    signals: list[Signal]
    entities: list[Entity]


class TopicSummary(BaseModel):
    id: str
    title: str
    description: str
    category: MarketCategory
    query: str
    stateVersion: str
    marketCount: int
    updateCount: int
    signalCount: int
    strongestMovementPercent: float
    strongestMovementDirection: MovementDirection
    latestUpdateAt: str | None = None


class TopicState(TopicSummary):
    markets: list[TopicMarket]
    updates: list[TopicUpdate]


class TopicDetail(TopicState):
    pass


class TopicsResponse(BaseModel):
    items: list[TopicSummary]
