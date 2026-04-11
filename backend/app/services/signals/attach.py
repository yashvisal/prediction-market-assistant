from __future__ import annotations

from dataclasses import replace
from typing import Any
from uuid import uuid4

from app.models.market import Entity, Signal
from app.services.events.types import EventWindow
from app.services.heuristics import HeuristicConfig
from app.services.persistence import SourceDocumentRecord
from app.services.provider_types import NormalizedHistoryPoint, NormalizedMarket
from app.services.signals.provider import SignalCandidate, build_signal_candidates


def attach_signals(
    *,
    market: NormalizedMarket,
    event: EventWindow,
    history: list[NormalizedHistoryPoint],
    event_id: str,
    heuristics: HeuristicConfig,
) -> tuple[list[Signal], list[SourceDocumentRecord], list[Entity], dict[str, Any], list[SignalCandidate]]:
    decision = route_research(market=market, event=event, heuristics=heuristics)
    if decision == "skip":
        return [], [], [], {"decision": decision, "reason": "movement below routing threshold", "candidate_count": 0}, []

    candidates = build_signal_candidates(market=market, event=event, history=history, heuristics=heuristics)
    kept_candidates = candidates[: heuristics.max_signals_per_event]
    entities: dict[str, Entity] = {}
    documents: list[SourceDocumentRecord] = []
    signals: list[Signal] = []

    for candidate in kept_candidates:
        document = replace(candidate.document, event_id=event_id)
        documents.append(document)
        for entity in candidate.entities:
            entities[entity.id] = entity

        signals.append(
            Signal(
                id=f"sig-{uuid4()}",
                title=candidate.title,
                source=candidate.source,
                sourceType=candidate.source_type,
                url=candidate.url,
                publishedAt=candidate.published_at,
                snippet=candidate.snippet,
                relevanceScore=candidate.relevance_score,
                entities=candidate.entities,
            )
        )

    return signals, documents, list(entities.values()), {
        "decision": decision,
        "reason": f"deterministic provider-backed {market.provider} sources",
        "candidate_count": len(candidates),
    }, [
        candidate if candidate in kept_candidates else replace(candidate, debug_payload={**candidate.debug_payload, "trimmed": True})
        for candidate in candidates
    ]


def route_research(*, market: NormalizedMarket, event: EventWindow, heuristics: HeuristicConfig) -> str:
    if event.movement_percent < heuristics.routing_skip_below:
        return "skip"
    if event.movement_percent < heuristics.routing_deep_at_or_above:
        return "light_research"
    return "deep_research"
