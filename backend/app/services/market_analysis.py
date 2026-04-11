from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from math import log1p
from statistics import pvariance
from typing import Any

from app.models.evaluation import (
    EventCandidateDebug,
    HeuristicEvaluationResponse,
    HeuristicEventOption,
    HistorySummary,
    MarketQualitySummary,
    RoutingDecisionDebug,
    SelectionDebugInfo,
    SignalCandidateDebug,
    ValidationMarketOption,
)
from app.models.market import MarketDetail, MarketEvent
from app.services.dome_markets import DomeHydratedMarket, hydrate_dome_market
from app.services.events.detector import evaluate_event_detection, stable_event_id
from app.services.heuristics import HeuristicConfig
from app.services.provider_types import MarketSeed, NormalizedHistoryPoint, NormalizedMarket, ProviderSelectionInputs
from app.services.signals.attach import attach_signals


@dataclass(frozen=True)
class MarketCandidateContext:
    pool: str
    raw_market: dict[str, Any]
    bundle: Any
    normalized_market: NormalizedMarket
    history: list[NormalizedHistoryPoint]
    quality_summary: MarketQualitySummary
    selection_debug: SelectionDebugInfo
    selection_inputs: ProviderSelectionInputs


def build_candidate_context(
    *,
    seed: MarketSeed,
    heuristics: HeuristicConfig,
) -> MarketCandidateContext:
    hydrated: DomeHydratedMarket = hydrate_dome_market(
        raw_market=seed.raw_market,
        raw_event=seed.raw_event,
        history_window_days=heuristics.history_window_days,
    )
    history = ensure_minimum_history(hydrated.normalized_market, seed.raw_market, hydrated.history)
    quality_summary = build_market_quality_summary(history, heuristics)
    selection_debug = build_selection_debug(hydrated.selection_inputs, quality_summary, seed.pool, heuristics)
    return MarketCandidateContext(
        pool=seed.pool,
        raw_market=seed.raw_market,
        bundle=hydrated.bundle,
        normalized_market=hydrated.normalized_market,
        history=history,
        quality_summary=quality_summary,
        selection_debug=selection_debug,
        selection_inputs=hydrated.selection_inputs,
    )


def build_market_quality_summary(
    history: list[NormalizedHistoryPoint],
    heuristics: HeuristicConfig,
) -> MarketQualitySummary:
    probabilities = [point.probability for point in history]
    non_zero_ratio = (
        sum(1 for probability in probabilities if probability > 0) / len(probabilities)
        if probabilities
        else 0.0
    )
    variance = pvariance(probabilities) if len(probabilities) > 1 else 0.0
    spread = max(probabilities) - min(probabilities) if probabilities else 0.0
    recent_movement = abs(probabilities[-1] - probabilities[0]) if len(probabilities) > 1 else 0.0
    has_real_history = any(not point.source.startswith("synthetic") for point in history)
    usable_detector_input = (
        len(history) >= heuristics.selection_min_points
        and non_zero_ratio >= heuristics.selection_min_non_zero_ratio
    )
    return MarketQualitySummary(
        pointCount=len(history),
        nonZeroPointRatio=round(non_zero_ratio, 4),
        probabilityVariance=round(variance, 6),
        probabilitySpread=round(spread, 4),
        recentMovement=round(recent_movement, 4),
        hasRealHistory=has_real_history,
        usableDetectorInput=usable_detector_input,
    )


def build_selection_debug(
    selection_inputs: ProviderSelectionInputs,
    quality: MarketQualitySummary,
    pool: str,
    heuristics: HeuristicConfig,
) -> SelectionDebugInfo:
    current_price_non_zero = selection_inputs.non_zero_price_fields > 0
    history_score = min(
        max(
            quality.pointCount / max(1, heuristics.selection_min_points),
            selection_inputs.history_coverage_ratio,
        ),
        1.0,
    )
    spread_penalty = min((selection_inputs.spread or 0.0) * 10, 1.0) * heuristics.selection_spread_penalty
    components = {
        "volume": round(min(log1p(selection_inputs.volume) / 10, 1.0) * heuristics.selection_volume_weight, 4),
        "openInterest": round(
            min(log1p(selection_inputs.liquidity) / 10, 1.0) * heuristics.selection_open_interest_weight,
            4,
        ),
        "eventVolume": round(
            min(log1p(selection_inputs.event_volume) / 12, 1.0) * heuristics.selection_event_volume_weight,
            4,
        ),
        "nonZeroRatio": round(quality.nonZeroPointRatio * heuristics.selection_non_zero_ratio_weight, 4),
        "recentMovement": round(quality.recentMovement * 10 * heuristics.selection_recent_movement_weight, 4),
        "history": round(history_score * heuristics.selection_history_weight, 4),
        "recentTrades": round(
            min(selection_inputs.recent_trade_count / max(1, heuristics.selection_min_recent_trades), 1.0)
            * heuristics.selection_recent_trade_weight,
            4,
        ),
        "orderbook": round(
            (1.0 if selection_inputs.has_orderbook else 0.0) * heuristics.selection_orderbook_weight,
            4,
        ),
        "titleQuality": round(
            selection_inputs.title_quality * heuristics.selection_title_quality_weight,
            4,
        ),
    }
    penalties: list[str] = []
    score = sum(components.values()) - spread_penalty
    if not current_price_non_zero:
        score -= heuristics.selection_zero_price_penalty
        penalties.append("all_zero_price_fields")
    if not quality.hasRealHistory:
        penalties.append("synthetic_only_history")
    if not quality.usableDetectorInput:
        penalties.append("weak_detector_input")
    if selection_inputs.recent_trade_count < heuristics.selection_min_recent_trades:
        penalties.append("low_trade_activity")
    if selection_inputs.history_coverage_ratio < heuristics.selection_min_history_coverage:
        penalties.append("thin_history_coverage")
    if selection_inputs.title_quality < 0.35:
        penalties.append("weak_title_specificity")
    if spread_penalty > 0:
        penalties.append("wide_spread")

    reasons = []
    if current_price_non_zero:
        reasons.append("non_zero_price_fields")
    if quality.hasRealHistory:
        reasons.append("has_real_history")
    if quality.recentMovement > 0:
        reasons.append("recent_movement_present")
    if quality.nonZeroPointRatio >= heuristics.selection_min_non_zero_ratio:
        reasons.append("non_zero_ratio_above_minimum")
    if selection_inputs.recent_trade_count >= heuristics.selection_min_recent_trades:
        reasons.append("recent_trade_activity")
    if selection_inputs.has_orderbook:
        reasons.append("orderbook_present")
    if selection_inputs.history_coverage_ratio >= heuristics.selection_min_history_coverage:
        reasons.append("history_coverage_above_minimum")
    if selection_inputs.title_quality >= 0.45:
        reasons.append("interpretable_title")

    return SelectionDebugInfo(
        score=round(score, 4),
        pool=pool,
        selected=False,
        reasons=reasons,
        penalties=penalties,
        components=components,
    )


def score_prefetch_candidate(
    prefetch_inputs: ProviderSelectionInputs,
    heuristics: HeuristicConfig,
) -> float:
    score = (
        min(log1p(prefetch_inputs.volume) / 10, 1.0) * heuristics.selection_volume_weight
        + min(log1p(prefetch_inputs.liquidity) / 10, 1.0) * heuristics.selection_open_interest_weight
        + min(log1p(prefetch_inputs.event_volume) / 12, 1.0) * heuristics.selection_event_volume_weight
        + prefetch_inputs.title_quality * heuristics.selection_title_quality_weight
    )
    return round(score, 4)


def rank_candidate_contexts(
    contexts: list[MarketCandidateContext],
    *,
    limit: int,
    validation_market_tickers: tuple[str, ...],
) -> tuple[list[MarketCandidateContext], list[MarketCandidateContext]]:
    ranked = sorted(contexts, key=lambda item: item.selection_debug.score, reverse=True)
    selected_ids: list[str] = []

    for ticker in validation_market_tickers:
        for context in ranked:
            if context.normalized_market.id == ticker and ticker not in selected_ids:
                selected_ids.append(ticker)
                break

    for context in ranked:
        market_id = context.normalized_market.id
        if market_id not in selected_ids:
            selected_ids.append(market_id)
        if len(selected_ids) >= limit:
            break

    updated: list[MarketCandidateContext] = []
    for index, context in enumerate(ranked, start=1):
        updated.append(
            replace(
                context,
                selection_debug=SelectionDebugInfo(
                    **{
                        **context.selection_debug.model_dump(),
                        "rank": index,
                        "selected": context.normalized_market.id in selected_ids,
                    }
                ),
            )
        )
    selected = [context for context in updated if context.normalized_market.id in selected_ids[:limit]]
    return updated, selected


def build_validation_market_options(
    contexts: list[MarketCandidateContext],
    heuristics: HeuristicConfig,
) -> list[ValidationMarketOption]:
    explicit_known_good = set(heuristics.validation_market_tickers)
    fallback_known_good = [
        context.normalized_market.id
        for context in contexts
        if context.quality_summary.usableDetectorInput and context.quality_summary.recentMovement > 0
    ][:5]
    known_good = explicit_known_good or set(fallback_known_good)
    options: list[ValidationMarketOption] = []
    for context in contexts[:12]:
        options.append(
            ValidationMarketOption(
                marketId=context.normalized_market.id,
                title=context.normalized_market.title,
                status=context.normalized_market.status.value,
                pool=context.pool,  # type: ignore[arg-type]
                eventId=context.normalized_market.provider_event_ticker or None,
                eventTitle=_event_title(context),
                score=context.selection_debug.score,
                selected=context.selection_debug.selected,
                knownGood=context.normalized_market.id in known_good,
            )
        )
    return options


def build_event_options(contexts: list[MarketCandidateContext]) -> list[HeuristicEventOption]:
    grouped: dict[str, list[MarketCandidateContext]] = {}
    for context in contexts:
        event_id = context.normalized_market.provider_event_ticker or context.normalized_market.id
        grouped.setdefault(event_id, []).append(context)

    events: list[HeuristicEventOption] = []
    for event_id, items in grouped.items():
        ranked_items = sorted(items, key=lambda item: item.selection_debug.score, reverse=True)
        representative = ranked_items[0]
        events.append(
            HeuristicEventOption(
                eventId=event_id,
                title=_event_title(representative) or representative.normalized_market.title,
                status=representative.normalized_market.status.value,
                pool=representative.pool,  # type: ignore[arg-type]
                score=round(sum(item.selection_debug.score for item in ranked_items[:2]) / min(len(ranked_items), 2), 4),
                marketCount=len(items),
            )
        )
    return sorted(events, key=lambda item: item.score, reverse=True)


def build_history_summary(history: list[NormalizedHistoryPoint], source: str) -> HistorySummary:
    probabilities = [point.probability for point in history]
    return HistorySummary(
        source=source,
        firstTimestamp=history[0].timestamp if history else None,
        lastTimestamp=history[-1].timestamp if history else None,
        minProbability=min(probabilities) if probabilities else None,
        maxProbability=max(probabilities) if probabilities else None,
        currentProbability=probabilities[-1] if probabilities else None,
        pointCount=len(history),
    )


def evaluate_market_context(
    *,
    context: MarketCandidateContext,
    heuristics: HeuristicConfig,
    validation_markets: list[ValidationMarketOption],
) -> HeuristicEvaluationResponse:
    detection = evaluate_event_detection(context.normalized_market, context.history, heuristics)
    final_events: list[MarketEvent] = []
    signal_candidates: list[SignalCandidateDebug] = []
    routing_decisions: list[RoutingDecisionDebug] = []

    for event_window in detection.final_events:
        event_id = stable_event_id(event_window)
        signals, _documents, entities, routing, candidates = attach_signals(
            market=context.normalized_market,
            event=event_window,
            history=context.history,
            event_id=event_id,
            heuristics=heuristics,
        )
        final_events.append(
            MarketEvent(
                id=event_id,
                marketId=context.normalized_market.id,
                title=event_window.title,
                startTime=event_window.start_time,
                endTime=event_window.end_time,
                probabilityBefore=event_window.probability_before,
                probabilityAfter=event_window.probability_after,
                movementPercent=event_window.movement_percent,
                direction=event_window.direction,
                signals=signals,
                entities=entities,
                relatedEvents=[],
                summary=event_window.summary,
            )
        )
        routing_decisions.append(
            RoutingDecisionDebug(
                eventId=event_id,
                decision=routing["decision"],
                reason=routing["reason"],
                candidateCount=routing["candidate_count"],
            )
        )
        signal_candidates.extend(
            [
                SignalCandidateDebug(
                    eventId=event_id,
                    title=candidate.title,
                    source=candidate.source,
                    sourceType=candidate.source_type,
                    url=candidate.url,
                    publishedAt=candidate.published_at,
                    snippet=candidate.snippet,
                    relevanceScore=candidate.relevance_score,
                    kept=not candidate.debug_payload.get("trimmed", False),
                    debugPayload=candidate.debug_payload,
                )
                for candidate in candidates
            ]
        )

    market_detail = MarketDetail(
        id=context.normalized_market.id,
        title=context.normalized_market.title,
        description=context.normalized_market.description,
        status=context.normalized_market.status,
        category=context.normalized_market.category,
        currentProbability=context.normalized_market.current_probability,
        previousClose=context.normalized_market.previous_close,
        volume=context.normalized_market.volume,
        liquidity=context.normalized_market.liquidity,
        createdAt=context.normalized_market.created_at,
        closesAt=context.normalized_market.closes_at,
        resolvedAt=context.normalized_market.resolved_at,
        resolution=context.normalized_market.resolution,  # type: ignore[arg-type]
        eventCount=len(final_events),
        lastEventAt=final_events[0].endTime if final_events else None,
    )

    return HeuristicEvaluationResponse(
        market=market_detail,
        historySummary=build_history_summary(context.history, context.bundle.history_source),
        marketQuality=context.quality_summary,
        selectionDebug=context.selection_debug,
        rawCandidates=[
            EventCandidateDebug(
                candidateId=candidate.candidate_id,
                stage="raw",
                kept=True,
                dropReason=None,
                title=candidate.title,
                startTime=candidate.start_time,
                endTime=candidate.end_time,
                probabilityBefore=candidate.probability_before,
                probabilityAfter=candidate.probability_after,
                movementPercent=candidate.movement_percent,
                direction=candidate.direction,
                debugPayload=candidate.debug_payload,
            )
            for candidate in detection.raw_candidates
        ],
        filteredCandidates=[
            EventCandidateDebug(
                candidateId=item.candidate.candidate_id,
                stage="filtered",
                kept=item.kept,
                dropReason=item.drop_reason,
                title=item.candidate.title,
                startTime=item.candidate.start_time,
                endTime=item.candidate.end_time,
                probabilityBefore=item.candidate.probability_before,
                probabilityAfter=item.candidate.probability_after,
                movementPercent=item.candidate.movement_percent,
                direction=item.candidate.direction,
                debugPayload=item.candidate.debug_payload,
            )
            for item in detection.filtered_candidates
        ],
        finalEvents=final_events,
        signalCandidates=signal_candidates,
        routingDecisions=routing_decisions,
        validationMarkets=validation_markets,
    )


def ensure_minimum_history(
    market: NormalizedMarket,
    raw_market: dict[str, Any],
    points: list[NormalizedHistoryPoint],
) -> list[NormalizedHistoryPoint]:
    if len(points) >= 2:
        return points

    latest_timestamp = _coerce_timestamp(
        raw_market.get("updated_time") or raw_market.get("end_time") or raw_market.get("close_time"),
        market.closes_at,
    )

    synthetic = [
        NormalizedHistoryPoint(
            market_id=market.id,
            timestamp=market.created_at,
            probability=market.previous_close,
            yes_bid=None,
            yes_ask=None,
            volume=None,
            open_interest=None,
            source="synthetic_baseline",
            metadata={"reason": "missing_candlesticks"},
        ),
        NormalizedHistoryPoint(
            market_id=market.id,
            timestamp=latest_timestamp,
            probability=market.current_probability,
            yes_bid=None,
            yes_ask=None,
            volume=market.volume,
            open_interest=market.liquidity,
            source="synthetic_latest",
            metadata={"reason": "missing_candlesticks"},
        ),
    ]
    return sorted(points + synthetic, key=lambda item: item.timestamp)


def _event_title(context: MarketCandidateContext) -> str | None:
    metadata = context.normalized_market.metadata
    event_title = metadata.get("event_title")
    return str(event_title) if event_title else None


def _coerce_timestamp(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(int(value), tz=UTC).isoformat().replace("+00:00", "Z")
    return str(value)
