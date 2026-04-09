from __future__ import annotations

from dataclasses import dataclass, replace
from math import log1p
from statistics import pvariance

from app.config import Settings
from app.models.evaluation import (
    EventCandidateDebug,
    HeuristicEvaluationResponse,
    HistorySummary,
    MarketQualitySummary,
    RoutingDecisionDebug,
    SelectionDebugInfo,
    SignalCandidateDebug,
    ValidationMarketOption,
)
from app.models.market import MarketDetail, MarketEvent
from app.services.events.detector import evaluate_event_detection, stable_event_id
from app.services.heuristics import HeuristicConfig
from app.services.kalshi.client import KalshiClient, KalshiMarketBundle
from app.services.kalshi.normalize import normalize_candlesticks, normalize_market
from app.services.kalshi.types import KalshiMarket, NormalizedHistoryPoint, NormalizedMarket
from app.services.signals.attach import attach_signals


@dataclass(frozen=True)
class MarketCandidateContext:
    pool: str
    raw_market: KalshiMarket
    bundle: KalshiMarketBundle
    normalized_market: NormalizedMarket
    history: list[NormalizedHistoryPoint]
    quality_summary: MarketQualitySummary
    selection_debug: SelectionDebugInfo


def build_candidate_context(
    *,
    raw_market: KalshiMarket,
    pool: str,
    client: KalshiClient,
    settings: Settings,
    heuristics: HeuristicConfig,
) -> MarketCandidateContext:
    bundle = client.get_market_bundle(raw_market, history_window_days=heuristics.history_window_days)
    normalized_market = normalize_market(bundle.raw_market, web_base_url=settings.kalshi_web_base_url)
    history = normalize_candlesticks(
        normalized_market.id,
        bundle.candlesticks,
        source=bundle.history_source,
    )
    history = ensure_minimum_history(normalized_market, raw_market, history)
    quality_summary = build_market_quality_summary(history, heuristics)
    selection_debug = build_selection_debug(raw_market, quality_summary, pool, heuristics)
    return MarketCandidateContext(
        pool=pool,
        raw_market=raw_market,
        bundle=bundle,
        normalized_market=normalized_market,
        history=history,
        quality_summary=quality_summary,
        selection_debug=selection_debug,
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
    raw_market: KalshiMarket,
    quality: MarketQualitySummary,
    pool: str,
    heuristics: HeuristicConfig,
) -> SelectionDebugInfo:
    volume_value = _float_value(raw_market.get("volume_fp"))
    open_interest_value = _float_value(raw_market.get("open_interest_fp"))
    current_price_non_zero = any(
        _float_value(raw_market.get(field)) > 0
        for field in (
            "last_price_dollars",
            "previous_price_dollars",
            "yes_bid_dollars",
            "yes_ask_dollars",
        )
    )
    components = {
        "volume": round(min(log1p(volume_value) / 8, 1.0) * heuristics.selection_volume_weight, 4),
        "openInterest": round(
            min(log1p(open_interest_value) / 8, 1.0) * heuristics.selection_open_interest_weight,
            4,
        ),
        "nonZeroRatio": round(quality.nonZeroPointRatio * heuristics.selection_non_zero_ratio_weight, 4),
        "recentMovement": round(quality.recentMovement * 10 * heuristics.selection_recent_movement_weight, 4),
        "history": round(
            min(quality.pointCount / max(1, heuristics.selection_min_points), 1.0)
            * heuristics.selection_history_weight,
            4,
        ),
    }
    penalties: list[str] = []
    score = sum(components.values())
    if not current_price_non_zero:
        score -= heuristics.selection_zero_price_penalty
        penalties.append("all_zero_price_fields")
    if not quality.hasRealHistory:
        penalties.append("synthetic_only_history")
    if not quality.usableDetectorInput:
        penalties.append("weak_detector_input")

    reasons = []
    if current_price_non_zero:
        reasons.append("non_zero_price_fields")
    if quality.hasRealHistory:
        reasons.append("has_real_history")
    if quality.recentMovement > 0:
        reasons.append("recent_movement_present")
    if quality.nonZeroPointRatio >= heuristics.selection_min_non_zero_ratio:
        reasons.append("non_zero_ratio_above_minimum")

    return SelectionDebugInfo(
        score=round(score, 4),
        pool=pool,
        selected=False,
        reasons=reasons,
        penalties=penalties,
        components=components,
    )


def score_prefetch_candidate(
    raw_market: KalshiMarket,
    heuristics: HeuristicConfig,
) -> float:
    volume_value = _float_value(raw_market.get("volume_fp"))
    open_interest_value = _float_value(raw_market.get("open_interest_fp"))
    non_zero_price_fields = sum(
        1
        for field in (
            "last_price_dollars",
            "previous_price_dollars",
            "yes_bid_dollars",
            "yes_ask_dollars",
        )
        if _float_value(raw_market.get(field)) > 0
    )
    score = (
        min(log1p(volume_value) / 8, 1.0) * heuristics.selection_volume_weight
        + min(log1p(open_interest_value) / 8, 1.0) * heuristics.selection_open_interest_weight
        + min(non_zero_price_fields / 2, 1.0) * 0.35
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
                score=context.selection_debug.score,
                selected=context.selection_debug.selected,
                knownGood=context.normalized_market.id in known_good,
            )
        )
    return options


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
    raw_market: KalshiMarket,
    points: list[NormalizedHistoryPoint],
) -> list[NormalizedHistoryPoint]:
    if len(points) >= 2:
        return points

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
            timestamp=raw_market.get("updated_time", market.closes_at),
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


def _float_value(value: str | None) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)
