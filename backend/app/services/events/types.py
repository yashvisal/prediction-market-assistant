from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.models.market import MovementDirection


DETECTOR_VERSION = "detector-v1"


@dataclass(frozen=True)
class EventWindow:
    market_id: str
    title: str
    start_time: str
    end_time: str
    probability_before: float
    probability_after: float
    movement_percent: float
    direction: MovementDirection
    summary: str
    debug_payload: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class EventCandidate:
    candidate_id: str
    title: str
    start_time: str
    end_time: str | None
    probability_before: float
    probability_after: float | None
    movement_percent: float
    direction: MovementDirection | None
    debug_payload: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class FilteredEventCandidate:
    candidate: EventCandidate
    stage: Literal["raw", "filtered", "final"]
    kept: bool
    drop_reason: str | None = None


@dataclass(frozen=True)
class DetectionEvaluation:
    raw_candidates: list[EventCandidate]
    filtered_candidates: list[FilteredEventCandidate]
    final_events: list[EventWindow]
