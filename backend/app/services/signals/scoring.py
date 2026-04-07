from __future__ import annotations

from datetime import datetime


def score_candidate(
    *,
    event_end_time: datetime,
    candidate_time: datetime,
    base_score: float,
) -> float:
    delta_seconds = abs((event_end_time - candidate_time).total_seconds())
    if delta_seconds <= 60 * 60:
        bonus = 0.12
    elif delta_seconds <= 6 * 60 * 60:
        bonus = 0.08
    elif delta_seconds <= 24 * 60 * 60:
        bonus = 0.04
    else:
        bonus = 0.0
    return round(min(0.99, base_score + bonus), 2)
