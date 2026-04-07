from __future__ import annotations

import hashlib
import json
from dataclasses import asdict

from app.config import Settings
from app.models.market import MovementDirection
from app.services.events.types import DETECTOR_VERSION, EventWindow
from app.services.kalshi.types import NormalizedHistoryPoint, NormalizedMarket


def detect_event_windows(
    market: NormalizedMarket,
    history: list[NormalizedHistoryPoint],
    settings: Settings,
) -> list[EventWindow]:
    if len(history) < 2:
        return []

    points = sorted(history, key=lambda item: item.timestamp)
    windows: list[EventWindow] = []
    start_index = 0

    while start_index < len(points) - 1:
        anchor = points[start_index]
        best_index: int | None = None
        best_delta = 0.0

        for index in range(start_index + 1, len(points)):
            delta = points[index].probability - anchor.probability
            if abs(delta) >= settings.event_threshold and abs(delta) >= abs(best_delta):
                best_index = index
                best_delta = delta

        if best_index is None:
            start_index += 1
            continue

        direction = MovementDirection.UP if best_delta >= 0 else MovementDirection.DOWN
        end_index = best_index

        for follow_index in range(best_index + 1, len(points)):
            follow_delta = points[follow_index].probability - anchor.probability
            same_direction = (follow_delta >= 0 and direction == MovementDirection.UP) or (
                follow_delta <= 0 and direction == MovementDirection.DOWN
            )
            if same_direction and abs(follow_delta) >= abs(best_delta):
                best_delta = follow_delta
                end_index = follow_index
            else:
                break

        before = anchor.probability
        after = points[end_index].probability
        movement = round(abs(after - before), 4)
        windows.append(
            EventWindow(
                market_id=market.id,
                title=_window_title(market.title, direction, movement),
                start_time=anchor.timestamp,
                end_time=points[end_index].timestamp,
                probability_before=round(before, 4),
                probability_after=round(after, 4),
                movement_percent=movement,
                direction=direction,
                summary=_window_summary(market.title, direction, before, after, anchor.timestamp, points[end_index].timestamp),
                debug_payload={
                    "anchor_index": start_index,
                    "end_index": end_index,
                    "threshold": settings.event_threshold,
                    "detector_version": DETECTOR_VERSION,
                },
            )
        )
        start_index = min(end_index + settings.event_cooldown_points, len(points) - 1)

    merged = _merge_overlaps(windows)
    return merged[: settings.max_events_per_market]


def stable_event_id(window: EventWindow) -> str:
    payload = f"{window.market_id}|{window.start_time}|{window.end_time}|{DETECTOR_VERSION}"
    return f"evt-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def revision_hash(window: EventWindow) -> str:
    payload = json.dumps(asdict(window), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _merge_overlaps(windows: list[EventWindow]) -> list[EventWindow]:
    if not windows:
        return []

    ordered = sorted(windows, key=lambda item: item.start_time)
    merged = [ordered[0]]
    for window in ordered[1:]:
        previous = merged[-1]
        overlaps = window.start_time <= previous.end_time and window.direction == previous.direction
        if not overlaps:
            merged.append(window)
            continue

        if window.movement_percent > previous.movement_percent:
            merged[-1] = window
    return sorted(merged, key=lambda item: item.start_time, reverse=True)


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
