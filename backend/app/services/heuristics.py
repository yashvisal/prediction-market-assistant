from __future__ import annotations

from dataclasses import dataclass, replace

from app.config import Settings


@dataclass(frozen=True)
class HeuristicConfig:
    tracked_market_limit: int
    historical_market_limit: int
    history_window_days: int
    event_threshold: float
    event_cooldown_points: int
    max_events_per_market: int
    max_signals_per_event: int
    routing_skip_below: float
    routing_deep_at_or_above: float
    scoring_base_rules: float
    scoring_base_snapshot: float
    scoring_bonus_1h: float
    scoring_bonus_6h: float
    scoring_bonus_24h: float
    selection_volume_weight: float
    selection_open_interest_weight: float
    selection_non_zero_ratio_weight: float
    selection_recent_movement_weight: float
    selection_history_weight: float
    selection_zero_price_penalty: float
    selection_candidate_pool_multiplier: int
    selection_min_points: int
    selection_min_non_zero_ratio: float
    validation_market_tickers: tuple[str, ...]


@dataclass(frozen=True)
class HeuristicOverrides:
    tracked_market_limit: int | None = None
    historical_market_limit: int | None = None
    history_window_days: int | None = None
    event_threshold: float | None = None
    event_cooldown_points: int | None = None
    max_events_per_market: int | None = None
    max_signals_per_event: int | None = None
    routing_skip_below: float | None = None
    routing_deep_at_or_above: float | None = None
    scoring_base_rules: float | None = None
    scoring_base_snapshot: float | None = None
    scoring_bonus_1h: float | None = None
    scoring_bonus_6h: float | None = None
    scoring_bonus_24h: float | None = None
    selection_volume_weight: float | None = None
    selection_open_interest_weight: float | None = None
    selection_non_zero_ratio_weight: float | None = None
    selection_recent_movement_weight: float | None = None
    selection_history_weight: float | None = None
    selection_zero_price_penalty: float | None = None
    selection_candidate_pool_multiplier: int | None = None
    selection_min_points: int | None = None
    selection_min_non_zero_ratio: float | None = None


def heuristics_from_settings(settings: Settings) -> HeuristicConfig:
    return HeuristicConfig(
        tracked_market_limit=settings.tracked_market_limit,
        historical_market_limit=settings.historical_market_limit,
        history_window_days=settings.history_window_days,
        event_threshold=settings.event_threshold,
        event_cooldown_points=settings.event_cooldown_points,
        max_events_per_market=settings.max_events_per_market,
        max_signals_per_event=settings.max_signals_per_event,
        routing_skip_below=0.03,
        routing_deep_at_or_above=0.08,
        scoring_base_rules=0.62,
        scoring_base_snapshot=0.70,
        scoring_bonus_1h=0.12,
        scoring_bonus_6h=0.08,
        scoring_bonus_24h=0.04,
        selection_volume_weight=0.45,
        selection_open_interest_weight=0.30,
        selection_non_zero_ratio_weight=1.35,
        selection_recent_movement_weight=1.60,
        selection_history_weight=0.85,
        selection_zero_price_penalty=0.90,
        selection_candidate_pool_multiplier=4,
        selection_min_points=6,
        selection_min_non_zero_ratio=0.15,
        validation_market_tickers=settings.validation_market_tickers,
    )


def apply_heuristic_overrides(
    base: HeuristicConfig,
    overrides: HeuristicOverrides | None,
) -> HeuristicConfig:
    if overrides is None:
        return base

    updates = {
        field: value
        for field, value in overrides.__dict__.items()
        if value is not None
    }
    if not updates:
        return base
    return replace(base, **updates)
