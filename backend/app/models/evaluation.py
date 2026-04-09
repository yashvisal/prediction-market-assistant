from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from app.models.market import MarketDetail, MarketEvent, MovementDirection, SignalSourceType


class MarketQualitySummary(BaseModel):
    pointCount: int
    nonZeroPointRatio: float
    probabilityVariance: float
    probabilitySpread: float
    recentMovement: float
    hasRealHistory: bool
    usableDetectorInput: bool


class SelectionDebugInfo(BaseModel):
    score: float
    rank: int | None = None
    pool: Literal["open", "historical"]
    selected: bool
    reasons: list[str]
    penalties: list[str]
    components: dict[str, float]


class ValidationMarketOption(BaseModel):
    marketId: str
    title: str
    status: str
    pool: Literal["open", "historical"]
    score: float
    selected: bool
    knownGood: bool


class HistorySummary(BaseModel):
    source: str
    firstTimestamp: str | None = None
    lastTimestamp: str | None = None
    minProbability: float | None = None
    maxProbability: float | None = None
    currentProbability: float | None = None
    pointCount: int


class EventCandidateDebug(BaseModel):
    candidateId: str
    stage: Literal["raw", "filtered", "final"]
    kept: bool
    dropReason: str | None = None
    title: str
    startTime: str
    endTime: str | None = None
    probabilityBefore: float
    probabilityAfter: float | None = None
    movementPercent: float
    direction: MovementDirection | None = None
    debugPayload: dict[str, object]


class SignalCandidateDebug(BaseModel):
    eventId: str
    title: str
    source: str
    sourceType: SignalSourceType
    url: str
    publishedAt: str
    snippet: str
    relevanceScore: float
    kept: bool
    debugPayload: dict[str, object]


class RoutingDecisionDebug(BaseModel):
    eventId: str
    decision: Literal["skip", "light_research", "deep_research"]
    reason: str
    candidateCount: int


class HeuristicEvaluationResponse(BaseModel):
    market: MarketDetail
    historySummary: HistorySummary
    marketQuality: MarketQualitySummary
    selectionDebug: SelectionDebugInfo
    rawCandidates: list[EventCandidateDebug]
    filteredCandidates: list[EventCandidateDebug]
    finalEvents: list[MarketEvent]
    signalCandidates: list[SignalCandidateDebug]
    routingDecisions: list[RoutingDecisionDebug]
    validationMarkets: list[ValidationMarketOption]


class HeuristicMarketListResponse(BaseModel):
    items: list[ValidationMarketOption]
