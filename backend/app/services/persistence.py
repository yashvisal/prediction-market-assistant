from __future__ import annotations
import json
from dataclasses import asdict, dataclass
from datetime import UTC
from typing import Any

import psycopg
from psycopg.rows import dict_row

from app.config import Settings
from app.models.market import (
    DashboardSnapshotResponse,
    Entity,
    MarketCategory,
    MarketDetail,
    MarketEvent,
    MarketEventFeedItem,
    MarketStatus,
    MovementDirection,
    RelatedEvent,
    Signal,
    SignalSourceType,
)
@dataclass(frozen=True)
class ArtifactRecord:
    id: str
    owner_type: str
    owner_id: str
    bucket: str
    object_key: str
    content_type: str
    checksum: str
    source_url: str | None
    parser_version: str
    captured_at: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class SourceDocumentRecord:
    id: str
    event_id: str
    market_id: str
    title: str
    source: str
    source_type: str
    url: str
    published_at: str
    snippet: str
    body_artifact_id: str | None
    checksum: str
    parser_version: str
    captured_at: str
    metadata: dict[str, Any]


class MarketStore:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._schema_ready = False

    def ensure_schema(self) -> None:
        if self._schema_ready:
            return

        ddl = """
        create table if not exists markets (
            id text primary key,
            provider text not null,
            provider_market_ticker text not null,
            provider_event_ticker text,
            title text not null,
            description text not null,
            status text not null,
            category text not null,
            current_probability double precision not null,
            previous_close double precision not null,
            volume bigint not null,
            liquidity bigint not null,
            created_at timestamptz not null,
            closes_at timestamptz not null,
            resolved_at timestamptz,
            resolution text,
            event_count integer not null default 0,
            last_event_at timestamptz,
            detail_url text,
            rules_primary text,
            rules_secondary text,
            metadata jsonb not null default '{}'::jsonb,
            updated_at timestamptz not null default now()
        );

        create table if not exists market_time_series (
            market_id text not null references markets(id) on delete cascade,
            timestamp timestamptz not null,
            probability double precision not null,
            yes_bid double precision,
            yes_ask double precision,
            volume bigint,
            open_interest bigint,
            source text not null,
            metadata jsonb not null default '{}'::jsonb,
            primary key (market_id, timestamp)
        );

        create table if not exists market_events (
            id text primary key,
            market_id text not null references markets(id) on delete cascade,
            title text not null,
            start_time timestamptz not null,
            end_time timestamptz not null,
            probability_before double precision not null,
            probability_after double precision not null,
            movement_percent double precision not null,
            direction text not null,
            summary text,
            entities_json jsonb not null default '[]'::jsonb,
            related_events_json jsonb not null default '[]'::jsonb,
            detector_version text not null,
            revision_hash text not null,
            debug_payload jsonb not null default '{}'::jsonb,
            updated_at timestamptz not null default now()
        );

        create table if not exists artifacts (
            id text primary key,
            owner_type text not null,
            owner_id text not null,
            bucket text not null,
            object_key text not null,
            content_type text not null,
            checksum text not null,
            source_url text,
            parser_version text not null,
            captured_at timestamptz not null,
            metadata jsonb not null default '{}'::jsonb
        );

        create table if not exists source_documents (
            id text primary key,
            event_id text not null references market_events(id) on delete cascade,
            market_id text not null references markets(id) on delete cascade,
            title text not null,
            source text not null,
            source_type text not null,
            url text not null,
            published_at timestamptz not null,
            snippet text not null,
            body_artifact_id text,
            checksum text not null,
            parser_version text not null,
            captured_at timestamptz not null,
            metadata jsonb not null default '{}'::jsonb
        );

        create table if not exists signal_records (
            id text primary key,
            event_id text not null references market_events(id) on delete cascade,
            document_id text references source_documents(id) on delete set null,
            title text not null,
            source text not null,
            source_type text not null,
            url text not null,
            published_at timestamptz not null,
            snippet text not null,
            relevance_score double precision not null,
            entities_json jsonb not null default '[]'::jsonb
        );

        create table if not exists research_runs (
            id text primary key,
            market_id text not null references markets(id) on delete cascade,
            event_id text references market_events(id) on delete cascade,
            decision text not null,
            status text not null,
            details jsonb not null default '{}'::jsonb,
            created_at timestamptz not null default now()
        );
        """

        with psycopg.connect(self._settings.supabase_db_url) as conn:
            conn.execute(ddl)
            conn.commit()

        self._schema_ready = True

    def _connect(self) -> psycopg.Connection[Any]:
        self.ensure_schema()
        return psycopg.connect(self._settings.supabase_db_url, row_factory=dict_row)

    def upsert_markets(self, markets: list[dict[str, Any]]) -> None:
        if not markets:
            return

        sql = """
        insert into markets (
            id, provider, provider_market_ticker, provider_event_ticker, title, description,
            status, category, current_probability, previous_close, volume, liquidity,
            created_at, closes_at, resolved_at, resolution, event_count, last_event_at,
            detail_url, rules_primary, rules_secondary, metadata, updated_at
        )
        values (
            %(id)s, %(provider)s, %(provider_market_ticker)s, %(provider_event_ticker)s, %(title)s, %(description)s,
            %(status)s, %(category)s, %(current_probability)s, %(previous_close)s, %(volume)s, %(liquidity)s,
            %(created_at)s, %(closes_at)s, %(resolved_at)s, %(resolution)s, %(event_count)s, %(last_event_at)s,
            %(detail_url)s, %(rules_primary)s, %(rules_secondary)s, %(metadata)s::jsonb, now()
        )
        on conflict (id) do update set
            provider = excluded.provider,
            provider_market_ticker = excluded.provider_market_ticker,
            provider_event_ticker = excluded.provider_event_ticker,
            title = excluded.title,
            description = excluded.description,
            status = excluded.status,
            category = excluded.category,
            current_probability = excluded.current_probability,
            previous_close = excluded.previous_close,
            volume = excluded.volume,
            liquidity = excluded.liquidity,
            created_at = excluded.created_at,
            closes_at = excluded.closes_at,
            resolved_at = excluded.resolved_at,
            resolution = excluded.resolution,
            event_count = excluded.event_count,
            last_event_at = excluded.last_event_at,
            detail_url = excluded.detail_url,
            rules_primary = excluded.rules_primary,
            rules_secondary = excluded.rules_secondary,
            metadata = excluded.metadata,
            updated_at = now()
        """

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.executemany(sql, markets)
            conn.commit()

    def replace_time_series(self, market_id: str, points: list[dict[str, Any]]) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("delete from market_time_series where market_id = %s", (market_id,))
                if points:
                    cur.executemany(
                        """
                        insert into market_time_series (
                            market_id, timestamp, probability, yes_bid, yes_ask,
                            volume, open_interest, source, metadata
                        )
                        values (
                            %(market_id)s, %(timestamp)s, %(probability)s, %(yes_bid)s, %(yes_ask)s,
                            %(volume)s, %(open_interest)s, %(source)s, %(metadata)s::jsonb
                        )
                        """,
                        points,
                    )
            conn.commit()

    def replace_market_events(
        self,
        market_id: str,
        events: list[dict[str, Any]],
        signals_by_event: dict[str, list[dict[str, Any]]],
        source_docs_by_event: dict[str, list[SourceDocumentRecord]],
    ) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("delete from market_events where market_id = %s", (market_id,))
                if events:
                    cur.executemany(
                        """
                        insert into market_events (
                            id, market_id, title, start_time, end_time, probability_before,
                            probability_after, movement_percent, direction, summary,
                            entities_json, related_events_json, detector_version,
                            revision_hash, debug_payload, updated_at
                        )
                        values (
                            %(id)s, %(market_id)s, %(title)s, %(start_time)s, %(end_time)s, %(probability_before)s,
                            %(probability_after)s, %(movement_percent)s, %(direction)s, %(summary)s,
                            %(entities_json)s::jsonb, %(related_events_json)s::jsonb, %(detector_version)s,
                            %(revision_hash)s, %(debug_payload)s::jsonb, now()
                        )
                        """,
                        events,
                    )
                    docs: list[dict[str, Any]] = []
                    sigs: list[dict[str, Any]] = []
                    for event in events:
                        event_id = event["id"]
                        docs.extend(
                            {
                                **asdict(doc),
                                "metadata": json.dumps(doc.metadata, sort_keys=True),
                            }
                            for doc in source_docs_by_event.get(event_id, [])
                        )
                        sigs.extend(signals_by_event.get(event_id, []))

                    if docs:
                        cur.executemany(
                            """
                            insert into source_documents (
                                id, event_id, market_id, title, source, source_type, url, published_at,
                                snippet, body_artifact_id, checksum, parser_version, captured_at, metadata
                            )
                            values (
                                %(id)s, %(event_id)s, %(market_id)s, %(title)s, %(source)s, %(source_type)s, %(url)s, %(published_at)s,
                                %(snippet)s, %(body_artifact_id)s, %(checksum)s, %(parser_version)s, %(captured_at)s, %(metadata)s::jsonb
                            )
                            on conflict (id) do update set
                                title = excluded.title,
                                source = excluded.source,
                                source_type = excluded.source_type,
                                url = excluded.url,
                                published_at = excluded.published_at,
                                snippet = excluded.snippet,
                                body_artifact_id = excluded.body_artifact_id,
                                checksum = excluded.checksum,
                                parser_version = excluded.parser_version,
                                captured_at = excluded.captured_at,
                                metadata = excluded.metadata
                            """,
                            docs,
                        )

                    if sigs:
                        cur.executemany(
                            """
                            insert into signal_records (
                                id, event_id, document_id, title, source, source_type, url,
                                published_at, snippet, relevance_score, entities_json
                            )
                            values (
                                %(id)s, %(event_id)s, %(document_id)s, %(title)s, %(source)s, %(source_type)s, %(url)s,
                                %(published_at)s, %(snippet)s, %(relevance_score)s, %(entities_json)s::jsonb
                            )
                            on conflict (id) do update set
                                document_id = excluded.document_id,
                                title = excluded.title,
                                source = excluded.source,
                                source_type = excluded.source_type,
                                url = excluded.url,
                                published_at = excluded.published_at,
                                snippet = excluded.snippet,
                                relevance_score = excluded.relevance_score,
                                entities_json = excluded.entities_json
                            """,
                            sigs,
                        )
            conn.commit()

    def record_research_runs(self, runs: list[dict[str, Any]]) -> None:
        if not runs:
            return
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    insert into research_runs (id, market_id, event_id, decision, status, details)
                    values (%(id)s, %(market_id)s, %(event_id)s, %(decision)s, %(status)s, %(details)s::jsonb)
                    on conflict (id) do update set
                        decision = excluded.decision,
                        status = excluded.status,
                        details = excluded.details
                    """,
                    runs,
                )
            conn.commit()

    def upsert_artifacts(self, artifacts: list[ArtifactRecord]) -> None:
        if not artifacts:
            return

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    insert into artifacts (
                        id, owner_type, owner_id, bucket, object_key, content_type,
                        checksum, source_url, parser_version, captured_at, metadata
                    )
                    values (
                        %(id)s, %(owner_type)s, %(owner_id)s, %(bucket)s, %(object_key)s, %(content_type)s,
                        %(checksum)s, %(source_url)s, %(parser_version)s, %(captured_at)s, %(metadata)s::jsonb
                    )
                    on conflict (id) do update set
                        bucket = excluded.bucket,
                        object_key = excluded.object_key,
                        content_type = excluded.content_type,
                        checksum = excluded.checksum,
                        source_url = excluded.source_url,
                        parser_version = excluded.parser_version,
                        captured_at = excluded.captured_at,
                        metadata = excluded.metadata
                    """,
                    [
                        {
                            **asdict(artifact),
                            "metadata": json.dumps(artifact.metadata, sort_keys=True),
                        }
                        for artifact in artifacts
                    ],
                )
            conn.commit()

    def list_market_details(
        self,
        *,
        status: MarketStatus | None = None,
        category: MarketCategory | None = None,
    ) -> list[MarketDetail]:
        clauses: list[str] = []
        params: list[Any] = []
        if status:
            clauses.append("status = %s")
            params.append(status.value)
        if category:
            clauses.append("category = %s")
            params.append(category.value)

        where_sql = f"where {' and '.join(clauses)}" if clauses else ""
        query = f"""
        select *
        from markets
        {where_sql}
        order by
            case when status = 'open' then 0 else 1 end,
            volume desc,
            closes_at asc
        """

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._market_detail_from_row(row) for row in rows]

    def get_market_detail(self, market_id: str) -> MarketDetail | None:
        with self._connect() as conn:
            row = conn.execute("select * from markets where id = %s", (market_id,)).fetchone()
        return self._market_detail_from_row(row) if row else None

    def list_market_events(self, market_id: str) -> list[MarketEvent]:
        with self._connect() as conn:
            event_rows = conn.execute(
                """
                select *
                from market_events
                where market_id = %s
                order by start_time desc
                """,
                (market_id,),
            ).fetchall()
            signal_rows = conn.execute(
                """
                select *
                from signal_records
                where event_id in (
                    select id from market_events where market_id = %s
                )
                order by published_at desc
                """,
                (market_id,),
            ).fetchall()

        signals_by_event: dict[str, list[Signal]] = {}
        for row in signal_rows:
            signals_by_event.setdefault(row["event_id"], []).append(
                Signal(
                    id=row["id"],
                    title=row["title"],
                    source=row["source"],
                    sourceType=SignalSourceType(row["source_type"]),
                    url=row["url"],
                    publishedAt=row["published_at"].astimezone(UTC).isoformat().replace("+00:00", "Z"),
                    snippet=row["snippet"],
                    relevanceScore=float(row["relevance_score"]),
                    entities=[Entity.model_validate(entity) for entity in row["entities_json"]],
                )
            )

        return [self._market_event_from_row(row, signals_by_event.get(row["id"], [])) for row in event_rows]

    def get_dashboard_snapshot(self) -> DashboardSnapshotResponse:
        markets = self.list_market_details()
        events = []
        for market in markets:
            for event in self.list_market_events(market.id):
                events.append(
                    MarketEventFeedItem(
                        **event.model_dump(),
                        marketTitle=market.title,
                        marketCategory=market.category,
                        marketStatus=market.status,
                    )
                )
        top_events = sorted(events, key=lambda item: abs(item.movementPercent), reverse=True)[:4]
        active_markets = [market for market in markets if market.status == MarketStatus.OPEN]
        return DashboardSnapshotResponse(activeMarkets=active_markets, topEvents=top_events)

    def has_markets(self) -> bool:
        with self._connect() as conn:
            row = conn.execute("select count(*) as count from markets").fetchone()
        return bool(row and row["count"])

    def _market_detail_from_row(self, row: dict[str, Any]) -> MarketDetail:
        return MarketDetail(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=MarketStatus(row["status"]),
            category=MarketCategory(row["category"]),
            currentProbability=float(row["current_probability"]),
            previousClose=float(row["previous_close"]),
            volume=int(row["volume"]),
            liquidity=int(row["liquidity"]),
            createdAt=row["created_at"].astimezone(UTC).isoformat().replace("+00:00", "Z"),
            closesAt=row["closes_at"].astimezone(UTC).isoformat().replace("+00:00", "Z"),
            resolvedAt=(
                row["resolved_at"].astimezone(UTC).isoformat().replace("+00:00", "Z")
                if row["resolved_at"]
                else None
            ),
            resolution=row["resolution"] or None,
            eventCount=int(row["event_count"]),
            lastEventAt=(
                row["last_event_at"].astimezone(UTC).isoformat().replace("+00:00", "Z")
                if row["last_event_at"]
                else None
            ),
        )

    def _market_event_from_row(self, row: dict[str, Any], signals: list[Signal]) -> MarketEvent:
        return MarketEvent(
            id=row["id"],
            marketId=row["market_id"],
            title=row["title"],
            startTime=row["start_time"].astimezone(UTC).isoformat().replace("+00:00", "Z"),
            endTime=row["end_time"].astimezone(UTC).isoformat().replace("+00:00", "Z"),
            probabilityBefore=float(row["probability_before"]),
            probabilityAfter=float(row["probability_after"]),
            movementPercent=float(row["movement_percent"]),
            direction=MovementDirection(row["direction"]),
            signals=signals,
            entities=[Entity.model_validate(entity) for entity in row["entities_json"]],
            relatedEvents=[RelatedEvent.model_validate(item) for item in row["related_events_json"]],
            summary=row["summary"],
        )
