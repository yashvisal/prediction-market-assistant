from __future__ import annotations

import hashlib
import json
from dataclasses import asdict

from app.services.heuristics import HeuristicConfig
from app.models.market import MovementDirection
from app.services.events.types import (
    DETECTOR_VERSION,
    DetectionEvaluation,
    EventCandidate,
    EventWindow,
    FilteredEventCandidate,
)
from app.services.kalshi.types import NormalizedHistoryPoint, NormalizedMarket


def detect_event_windows(
    market: NormalizedMarket,
    history: list[NormalizedHistoryPoint],
    heuristics: HeuristicConfig,
) -> list[EventWindow]:
    return evaluate_event_detection(market, history, heuristics).final_events


def evaluate_event_detection(
    market: NormalizedMarket,
    history: list[NormalizedHistoryPoint],
    heuristics: HeuristicConfig,
) -> DetectionEvaluation:
    if len(history) < 2:
        return DetectionEvaluation(raw_candidates=[], filtered_candidates=[], final_events=[])

    points = sorted(history, key=lambda item: item.timestamp)
    raw_candidates = _build_raw_candidates(market, points)
    filtered_candidates, final_events = _filter_candidates(market, raw_candidates, heuristics)
    return DetectionEvaluation(
        raw_candidates=raw_candidates,
        filtered_candidates=filtered_candidates,
        final_events=final_events,
    )


def stable_event_id(window: EventWindow) -> str:
    payload = f"{window.market_id}|{window.start_time}|{window.end_time}|{DETECTOR_VERSION}"
    return f"evt-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def revision_hash(window: EventWindow) -> str:
    payload = json.dumps(asdict(window), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _build_raw_candidates(
    market: NormalizedMarket,
    points: list[NormalizedHistoryPoint],
) -> list[EventCandidate]:
    candidates: list[EventCandidate] = []
    for start_index, anchor in enumerate(points[:-1]):
        best_index = start_index + 1
        best_delta = points[best_index].probability - anchor.probability

        for index in range(start_index + 1, len(points)):
            delta = points[index].probability - anchor.probability
            if abs(delta) >= abs(best_delta):
                best_index = index
                best_delta = delta

        direction = None
        if best_delta > 0:
            direction = MovementDirection.UP
        elif best_delta < 0:
            direction = MovementDirection.DOWN

        end_point = points[best_index]
        movement = round(abs(best_delta), 4)
        candidates.append(
            EventCandidate(
                candidate_id=f"cand-{start_index}-{best_index}",
                title=_window_title(market.title, direction or MovementDirection.UP, movement),
                start_time=anchor.timestamp,
                end_time=end_point.timestamp,
                probability_before=round(anchor.probability, 4),
                probability_after=round(end_point.probability, 4),
                movement_percent=movement,
                direction=direction,
                debug_payload={
                    "anchor_index": start_index,
                    "end_index": best_index,
                    "detector_version": DETECTOR_VERSION,
                },
            )
        )
    return candidates


def _filter_candidates(
    market: NormalizedMarket,
    raw_candidates: list[EventCandidate],
    heuristics: HeuristicConfig,
) -> tuple[list[FilteredEventCandidate], list[EventWindow]]:
    filtered: list[FilteredEventCandidate] = []
    kept: list[EventCandidate] = []
    next_allowed_anchor = 0

    for candidate in raw_candidates:
        anchor_index = int(candidate.debug_payload["anchor_index"])
        if candidate.movement_percent < heuristics.event_threshold or candidate.direction is None:
            filtered.append(
                FilteredEventCandidate(
                    candidate=candidate,
                    stage="filtered",
                    kept=False,
                    drop_reason="threshold",
                )
            )
            continue

        if anchor_index < next_allowed_anchor:
            filtered.append(
                FilteredEventCandidate(
                    candidate=candidate,
                    stage="filtered",
                    kept=False,
                    drop_reason="cooldown",
                )
            )
            continue

        merged = False
        for index, existing in enumerate(list(kept)):
            overlaps = candidate.start_time <= (existing.end_time or candidate.end_time) and candidate.direction == existing.direction
            if not overlaps:
                continue
            merged = True
            if candidate.movement_percent > existing.movement_percent:
                filtered.append(
                    FilteredEventCandidate(
                        candidate=existing,
                        stage="filtered",
                        kept=False,
                        drop_reason="merge",
                    )
                )
                kept[index] = candidate
                filtered.append(
                    FilteredEventCandidate(
                        candidate=candidate,
                        stage="filtered",
                        kept=True,
                        drop_reason=None,
                    )
                )
            else:
                filtered.append(
                    FilteredEventCandidate(
                        candidate=candidate,
                        stage="filtered",
                        kept=False,
                        drop_reason="merge",
                    )
                )
            break

        if merged:
            continue

        kept.append(candidate)
        filtered.append(
            FilteredEventCandidate(
                candidate=candidate,
                stage="filtered",
                kept=True,
                drop_reason=None,
            )
        )
        next_allowed_anchor = anchor_index + heuristics.event_cooldown_points

    ordered_kept = sorted(kept, key=lambda item: item.start_time, reverse=True)
    final_candidates = ordered_kept[: heuristics.max_events_per_market]
    capped_out = {candidate.candidate_id for candidate in ordered_kept[heuristics.max_events_per_market :]}
    if capped_out:
        filtered = [
            FilteredEventCandidate(
                candidate=item.candidate,
                stage=item.stage,
                kept=False,
                drop_reason="cap",
            )
            if item.candidate.candidate_id in capped_out
            else item
            for item in filtered
        ]
        final_candidates = [candidate for candidate in final_candidates if candidate.candidate_id not in capped_out]

    final_events = [
        EventWindow(
            market_id=market.id,
            title=candidate.title,
            start_time=candidate.start_time,
            end_time=candidate.end_time or candidate.start_time,
            probability_before=candidate.probability_before,
            probability_after=candidate.probability_after or candidate.probability_before,
            movement_percent=candidate.movement_percent,
            direction=candidate.direction or MovementDirection.UP,
            summary=_window_summary(
                market.title,
                candidate.direction or MovementDirection.UP,
                candidate.probability_before,
                candidate.probability_after or candidate.probability_before,
                candidate.start_time,
                candidate.end_time or candidate.start_time,
            ),
            debug_payload={**candidate.debug_payload, "threshold": heuristics.event_threshold},
        )
        for candidate in final_candidates
    ]
    return filtered, final_events


def _window_title(title: str, direction: MovementDirection, movement: float) -> str:
    verb = "rose" if direction == MovementDirection.UP else "fell"
    return f"{title} {verb} {movement:.0%} over the detected window".replace("100%%", "100%")


def _window_summary(
    title: str,
    direction: MovementDirection,
    before: float,
    after: float,
    start_time: str,
    end_time: str,
) -> str:
    direction_text = "up" if direction == MovementDirection.UP else "down"
    return (
        f"{title} moved {direction_text} from {before:.0%} to {after:.0%} "
        f"between {start_time} and {end_time}."
    )
