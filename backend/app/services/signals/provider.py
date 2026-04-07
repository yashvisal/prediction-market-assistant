from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.config import Settings
from app.models.market import Entity, EntityType, SignalSourceType
from app.services.events.types import EventWindow
from app.services.kalshi.types import NormalizedHistoryPoint, NormalizedMarket
from app.services.persistence import SourceDocumentRecord
from app.services.signals.scoring import score_candidate


@dataclass(frozen=True)
class SignalCandidate:
    document: SourceDocumentRecord
    title: str
    source: str
    source_type: SignalSourceType
    url: str
    published_at: str
    snippet: str
    relevance_score: float
    entities: list[Entity]


def build_signal_candidates(
    *,
    market: NormalizedMarket,
    event: EventWindow,
    history: list[NormalizedHistoryPoint],
    settings: Settings,
) -> list[SignalCandidate]:
    event_end = datetime.fromisoformat(event.end_time.replace("Z", "+00:00")).astimezone(UTC)
    topic_entity = Entity(
        id=f"ent-{market.id.lower()}",
        name=market.title,
        type=EntityType.TOPIC,
    )
    candidates: list[SignalCandidate] = []

    if market.rules_primary:
        published_at = market.created_at
        document = SourceDocumentRecord(
            id=f"doc-{uuid4()}",
            event_id="",
            market_id=market.id,
            title=f"Kalshi rules for {market.title}",
            source="Kalshi",
            source_type=SignalSourceType.OFFICIAL.value,
            url=market.detail_url,
            published_at=published_at,
            snippet=market.rules_primary[:280],
            body_artifact_id=None,
            checksum=f"rules-{market.id}",
            parser_version="signal-provider-v1",
            captured_at=event.end_time,
            metadata={"kind": "market_rules"},
        )
        candidates.append(
            SignalCandidate(
                document=document,
                title=document.title,
                source=document.source,
                source_type=SignalSourceType.OFFICIAL,
                url=document.url,
                published_at=published_at,
                snippet=document.snippet,
                relevance_score=score_candidate(
                    event_end_time=event_end,
                    candidate_time=datetime.fromisoformat(published_at.replace("Z", "+00:00")).astimezone(UTC),
                    base_score=0.62,
                ),
                entities=[topic_entity],
            )
        )

    matching_points = [point for point in history if event.start_time <= point.timestamp <= event.end_time]
    if matching_points:
        latest = matching_points[-1]
        document = SourceDocumentRecord(
            id=f"doc-{uuid4()}",
            event_id="",
            market_id=market.id,
            title=f"Kalshi market snapshot near {event.title}",
            source="Kalshi Market Data",
            source_type=SignalSourceType.ANALYSIS.value,
            url=market.detail_url,
            published_at=latest.timestamp,
            snippet=(
                f"Observed probability {latest.probability:.0%}, YES bid "
                f"{latest.yes_bid if latest.yes_bid is not None else 'n/a'}, "
                f"YES ask {latest.yes_ask if latest.yes_ask is not None else 'n/a'}."
            ),
            body_artifact_id=None,
            checksum=f"snapshot-{market.id}-{latest.timestamp}",
            parser_version="signal-provider-v1",
            captured_at=latest.timestamp,
            metadata={"kind": "market_snapshot", "source": latest.source},
        )
        candidates.append(
            SignalCandidate(
                document=document,
                title=document.title,
                source=document.source,
                source_type=SignalSourceType.ANALYSIS,
                url=document.url,
                published_at=latest.timestamp,
                snippet=document.snippet,
                relevance_score=score_candidate(
                    event_end_time=event_end,
                    candidate_time=datetime.fromisoformat(latest.timestamp.replace("Z", "+00:00")).astimezone(UTC),
                    base_score=0.7,
                ),
                entities=[topic_entity],
            )
        )

    ordered = sorted(candidates, key=lambda item: item.relevance_score, reverse=True)
    return ordered[: settings.max_signals_per_event]
