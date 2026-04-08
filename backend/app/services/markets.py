from __future__ import annotations

import json
from datetime import UTC, datetime
from functools import lru_cache
from threading import Lock
from uuid import uuid4

from app.config import Settings, get_settings
from app.data.mock_markets import get_market as get_mock_market
from app.data.mock_markets import get_market_events as get_mock_market_events
from app.data.mock_markets import list_markets as list_mock_markets
from app.models.market import (
    DashboardSnapshotResponse,
    MarketCategory,
    MarketDetail,
    MarketEventFeedItem,
    MarketStatus,
)
from app.services.artifacts import ArtifactStore
from app.services.events.detector import detect_event_windows, revision_hash, stable_event_id
from app.services.kalshi.client import KalshiClient
from app.services.kalshi.normalize import normalize_candlesticks, normalize_market
from app.services.kalshi.types import KalshiMarket, NormalizedHistoryPoint, NormalizedMarket
from app.services.persistence import MarketStore
from app.services.signals.attach import attach_signals


_SYNC_LOCK = Lock()
_LAST_SYNC_AT: datetime | None = None


@lru_cache(maxsize=1)
def _settings() -> Settings:
    return get_settings()


@lru_cache(maxsize=1)
def _store() -> MarketStore:
    return MarketStore(_settings())


@lru_cache(maxsize=1)
def _artifact_store() -> ArtifactStore:
    return ArtifactStore(_settings())


@lru_cache(maxsize=1)
def _kalshi_client() -> KalshiClient:
    return KalshiClient(_settings())


def initialize_runtime() -> None:
    _store().ensure_schema()


def list_market_summaries(
    *, status: MarketStatus | None = None, category: MarketCategory | None = None
):
    _ensure_runtime_data()
    try:
        items = _store().list_market_details(status=status, category=category)
        if items or _store().has_markets():
            return items
    except Exception:
        pass
    return list_mock_markets(status=status, category=category)


def get_market_detail(market_id: str) -> MarketDetail | None:
    _ensure_runtime_data()
    try:
        market = _store().get_market_detail(market_id)
        if market:
            return market
    except Exception:
        pass
    return get_mock_market(market_id)


def list_market_events(market_id: str):
    _ensure_runtime_data()
    try:
        events = _store().list_market_events(market_id)
        if events or _store().get_market_detail(market_id) is not None:
            return events
    except Exception:
        pass
    return get_mock_market_events(market_id)


def get_dashboard_snapshot() -> DashboardSnapshotResponse:
    _ensure_runtime_data()
    try:
        snapshot = _store().get_dashboard_snapshot()
        if snapshot.activeMarkets or snapshot.topEvents or _store().has_markets():
            return snapshot
    except Exception:
        pass

    markets = list_market_summaries()
    events = []
    for market in markets:
        for event in list_market_events(market.id):
            events.append(
                MarketEventFeedItem(
                    **event.model_dump(),
                    marketTitle=market.title,
                    marketCategory=market.category,
                    marketStatus=market.status,
                )
            )
    top_events = sorted(events, key=lambda item: abs(item.movementPercent), reverse=True)[:4]
    return DashboardSnapshotResponse(
        activeMarkets=[market for market in markets if market.status == MarketStatus.OPEN],
        topEvents=top_events,
    )


def _ensure_runtime_data() -> None:
    global _LAST_SYNC_AT

    settings = _settings()
    if not settings.persistence_enabled:
        return

    now = datetime.now(UTC)
    if _LAST_SYNC_AT and (now - _LAST_SYNC_AT).total_seconds() < settings.sync_interval_seconds:
        return

    with _SYNC_LOCK:
        if _LAST_SYNC_AT and (datetime.now(UTC) - _LAST_SYNC_AT).total_seconds() < settings.sync_interval_seconds:
            return
        _sync_pipeline()
        _LAST_SYNC_AT = datetime.now(UTC)


def _sync_pipeline() -> None:
    settings = _settings()
    store = _store()
    artifact_store = _artifact_store()
    client = _kalshi_client()

    open_markets = client.list_markets(limit=max(settings.tracked_market_limit * 3, 20), status="open")
    open_markets = sorted(open_markets, key=lambda item: float(item.get("volume_fp") or 0), reverse=True)[
        : settings.tracked_market_limit
    ]
    historical_markets = client.list_historical_markets(limit=settings.historical_market_limit)
    historical_markets = sorted(
        historical_markets, key=lambda item: float(item.get("volume_fp") or 0), reverse=True
    )[: settings.historical_market_limit]

    market_rows = []
    artifacts = []
    research_runs = []

    for raw_market in _dedupe_markets(open_markets + historical_markets):
        bundle = client.get_market_bundle(raw_market)
        normalized_market = normalize_market(bundle.raw_market, web_base_url=settings.kalshi_web_base_url)
        history = normalize_candlesticks(
            normalized_market.id,
            bundle.candlesticks,
            source=bundle.history_source,
        )
        history = _ensure_minimum_history(normalized_market, raw_market, history)
        detected_events = detect_event_windows(normalized_market, history, settings)

        market_artifact = artifact_store.put_json(
            owner_type="market",
            owner_id=normalized_market.id,
            artifact_type="metadata",
            payload=bundle.raw_market,
            captured_at=datetime.now(UTC),
            source_url=f"{settings.kalshi_api_base_url}/markets",
            metadata={"provider": "kalshi"},
        )
        history_artifact = artifact_store.put_json(
            owner_type="market",
            owner_id=normalized_market.id,
            artifact_type="candlesticks",
            payload={"ticker": normalized_market.id, "candlesticks": bundle.candlesticks},
            captured_at=datetime.now(UTC),
            source_url=normalized_market.detail_url,
            metadata={"provider": "kalshi", "history_source": bundle.history_source},
        )
        artifacts.extend([market_artifact.record, history_artifact.record])

        event_rows = []
        signals_by_event: dict[str, list[dict[str, object]]] = {}
        docs_by_event = {}
        last_event_at = None

        for window in detected_events:
            event_id = stable_event_id(window)
            signals, documents, entities, routing = attach_signals(
                market=normalized_market,
                event=window,
                history=history,
                event_id=event_id,
                settings=settings,
            )
            docs_by_event[event_id] = documents
            signals_by_event[event_id] = [
                {
                    "id": signal.id,
                    "event_id": event_id,
                    "document_id": _match_document_id(signal.url, signal.title, documents),
                    "title": signal.title,
                    "source": signal.source,
                    "source_type": signal.sourceType.value,
                    "url": signal.url,
                    "published_at": signal.publishedAt,
                    "snippet": signal.snippet,
                    "relevance_score": signal.relevanceScore,
                    "entities_json": _json(signal.entities),
                }
                for signal in signals
            ]
            event_rows.append(
                {
                    "id": event_id,
                    "market_id": normalized_market.id,
                    "title": window.title,
                    "start_time": window.start_time,
                    "end_time": window.end_time,
                    "probability_before": window.probability_before,
                    "probability_after": window.probability_after,
                    "movement_percent": window.movement_percent,
                    "direction": window.direction.value,
                    "summary": window.summary,
                    "entities_json": _json(entities),
                    "related_events_json": "[]",
                    "detector_version": "detector-v1",
                    "revision_hash": revision_hash(window),
                    "debug_payload": _json(window.debug_payload),
                }
            )
            research_runs.append(
                {
                    "id": f"run-{uuid4()}",
                    "market_id": normalized_market.id,
                    "event_id": event_id,
                    "decision": routing["decision"],
                    "status": "completed",
                    "details": _json(routing),
                }
            )
            last_event_at = max(last_event_at or window.end_time, window.end_time)

        market_rows.append(
            {
                "id": normalized_market.id,
                "provider": normalized_market.provider,
                "provider_market_ticker": normalized_market.provider_market_ticker,
                "provider_event_ticker": normalized_market.provider_event_ticker,
                "title": normalized_market.title,
                "description": normalized_market.description,
                "status": normalized_market.status.value,
                "category": normalized_market.category.value,
                "current_probability": normalized_market.current_probability,
                "previous_close": normalized_market.previous_close,
                "volume": normalized_market.volume,
                "liquidity": normalized_market.liquidity,
                "created_at": normalized_market.created_at,
                "closes_at": normalized_market.closes_at,
                "resolved_at": normalized_market.resolved_at,
                "resolution": normalized_market.resolution,
                "event_count": len(event_rows),
                "last_event_at": last_event_at,
                "detail_url": normalized_market.detail_url,
                "rules_primary": normalized_market.rules_primary,
                "rules_secondary": normalized_market.rules_secondary,
                "metadata": _json(normalized_market.metadata),
            }
        )

        store.upsert_markets([market_rows[-1]])
        store.replace_time_series(normalized_market.id, [_history_row(point) for point in history])
        store.replace_market_events(normalized_market.id, event_rows, signals_by_event, docs_by_event)

    store.upsert_artifacts(artifacts)
    store.record_research_runs(research_runs)


def _ensure_minimum_history(
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


def _history_row(point: NormalizedHistoryPoint) -> dict[str, object]:
    return {
        "market_id": point.market_id,
        "timestamp": point.timestamp,
        "probability": point.probability,
        "yes_bid": point.yes_bid,
        "yes_ask": point.yes_ask,
        "volume": point.volume,
        "open_interest": point.open_interest,
        "source": point.source,
        "metadata": _json(point.metadata),
    }


def _json(value: object) -> str:
    if isinstance(value, list):
        return json.dumps(
            [item.model_dump() if hasattr(item, "model_dump") else item for item in value],
            sort_keys=True,
        )
    if hasattr(value, "model_dump"):
        return json.dumps(value.model_dump(), sort_keys=True)
    return json.dumps(value, sort_keys=True)


def _dedupe_markets(markets: list[KalshiMarket]) -> list[KalshiMarket]:
    deduped: dict[str, KalshiMarket] = {}
    for market in markets:
        deduped[market["ticker"]] = market
    return list(deduped.values())


def _match_document_id(url: str, title: str, documents) -> str | None:
    for document in documents:
        if document.url == url and document.title == title:
            return document.id
    return documents[0].id if documents else None
