from __future__ import annotations

from dataclasses import replace
from typing import Any
from uuid import uuid4

from app.config import Settings
from app.models.market import Entity, Signal
from app.services.events.types import EventWindow
from app.services.kalshi.types import NormalizedHistoryPoint, NormalizedMarket
from app.services.persistence import SourceDocumentRecord
from app.services.signals.provider import build_signal_candidates


def attach_signals(
    *,
    market: NormalizedMarket,
    event: EventWindow,
    history: list[NormalizedHistoryPoint],
    event_id: str,
    settings: Settings,
) -> tuple[list[Signal], list[SourceDocumentRecord], list[Entity], dict[str, Any]]:
    decision = route_research(market=market, event=event)
    if decision == "skip":
        return [], [], [], {"decision": decision, "reason": "movement below routing threshold"}

    candidates = build_signal_candidates(market=market, event=event, history=history, settings=settings)
    entities: dict[str, Entity] = {}
    documents: list[SourceDocumentRecord] = []
    signals: list[Signal] = []

    for candidate in candidates:
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
        "reason": "deterministic provider-backed Kalshi sources",
        "candidate_count": len(candidates),
    }


def route_research(*, market: NormalizedMarket, event: EventWindow) -> str:
    if event.movement_percent < 0.03:
        return "skip"
    if event.movement_percent < 0.08:
        return "light_research"
    return "deep_research"
