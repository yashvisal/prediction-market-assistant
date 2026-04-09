from __future__ import annotations

from datetime import datetime

from app.services.heuristics import HeuristicConfig


def score_candidate(
    *,
    event_end_time: datetime,
    candidate_time: datetime,
    base_score: float,
    heuristics: HeuristicConfig,
) -> float:
    delta_seconds = abs((event_end_time - candidate_time).total_seconds())
    if delta_seconds <= 60 * 60:
        bonus = heuristics.scoring_bonus_1h
    elif delta_seconds <= 6 * 60 * 60:
        bonus = heuristics.scoring_bonus_6h
    elif delta_seconds <= 24 * 60 * 60:
        bonus = heuristics.scoring_bonus_24h
    else:
        bonus = 0.0
    return round(min(0.99, base_score + bonus), 2)
