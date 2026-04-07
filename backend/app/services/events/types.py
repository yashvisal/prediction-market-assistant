from __future__ import annotations

from dataclasses import dataclass, field

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
