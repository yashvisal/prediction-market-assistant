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
from app.models.evaluation import HeuristicEvaluationResponse, HeuristicMarketListResponse
from app.models.market import (
    DashboardSnapshotResponse,
    MarketCategory,
    MarketDetail,
    MarketEventFeedItem,
    MarketStatus,
)
from app.services.artifacts import ArtifactStore
from app.services.events.detector import detect_event_windows, revision_hash, stable_event_id
from app.services.heuristics import (
    HeuristicConfig,
    HeuristicOverrides,
    apply_heuristic_overrides,
    heuristics_from_settings,
)
from app.services.kalshi.client import KalshiClient
from app.services.market_analysis import (
    MarketCandidateContext,
    build_candidate_context,
    build_validation_market_options,
    evaluate_market_context,
    rank_candidate_contexts,
    score_prefetch_candidate,
)
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


def list_heuristic_market_options() -> HeuristicMarketListResponse:
    heuristics = heuristics_from_settings(_settings())
    ranked = _load_ranked_candidate_contexts(heuristics)
    return HeuristicMarketListResponse(items=build_validation_market_options(ranked, heuristics))


def evaluate_market_heuristics(
    market_id: str,
    overrides: HeuristicOverrides | None = None,
) -> HeuristicEvaluationResponse:
    settings = _settings()
    heuristics = apply_heuristic_overrides(heuristics_from_settings(settings), overrides)
    ranked_contexts = _load_ranked_candidate_contexts(heuristics)
    validation_markets = build_validation_market_options(ranked_contexts, heuristics)
    context = next((item for item in ranked_contexts if item.normalized_market.id == market_id), None)
    if context is None:
        context = _load_market_context_by_id(market_id, heuristics)
        if context is None:
            raise KeyError(f"Market not found for heuristic evaluation: {market_id}")
    return evaluate_market_context(context=context, heuristics=heuristics, validation_markets=validation_markets)


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
    heuristics = heuristics_from_settings(settings)
    store = _store()
    artifact_store = _artifact_store()
    artifacts = []
    research_runs = []

    for context in _load_selected_candidate_contexts(heuristics):
        market_artifact = artifact_store.put_json(
            owner_type="market",
            owner_id=context.normalized_market.id,
            artifact_type="metadata",
            payload=context.bundle.raw_market,
            captured_at=datetime.now(UTC),
            source_url=f"{settings.kalshi_api_base_url}/markets",
            metadata={"provider": "kalshi"},
        )
        history_artifact = artifact_store.put_json(
            owner_type="market",
            owner_id=context.normalized_market.id,
            artifact_type="candlesticks",
            payload={"ticker": context.normalized_market.id, "candlesticks": context.bundle.candlesticks},
            captured_at=datetime.now(UTC),
            source_url=context.normalized_market.detail_url,
            metadata={"provider": "kalshi", "history_source": context.bundle.history_source},
        )
        artifacts.extend([market_artifact.record, history_artifact.record])

        event_windows = detect_event_windows(context.normalized_market, context.history, heuristics)
        event_rows = []
        signals_by_event: dict[str, list[dict[str, object]]] = {}
        docs_by_event = {}
        last_event_at = None

        for window in event_windows:
            event_id = stable_event_id(window)
            signals, documents, entities, routing, _candidates = attach_signals(
                market=context.normalized_market,
                event=window,
                history=context.history,
                event_id=event_id,
                heuristics=heuristics,
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
                    "market_id": context.normalized_market.id,
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
                    "market_id": context.normalized_market.id,
                    "event_id": event_id,
                    "decision": routing["decision"],
                    "status": "completed",
                    "details": _json(routing),
                }
            )
            last_event_at = max(last_event_at or window.end_time, window.end_time)

        market_row = _market_row(context=context, last_event_at=last_event_at, event_count=len(event_rows))
        store.upsert_markets([market_row])
        store.replace_time_series(context.normalized_market.id, [_history_row(point) for point in context.history])
        store.replace_market_events(context.normalized_market.id, event_rows, signals_by_event, docs_by_event)

    store.upsert_artifacts(artifacts)
    store.record_research_runs(research_runs)

def _history_row(point) -> dict[str, object]:
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

def _match_document_id(url: str, title: str, documents) -> str | None:
    for document in documents:
        if document.url == url and document.title == title:
            return document.id
    return documents[0].id if documents else None


def _shortlist_raw_markets(
    raw_markets: list[dict[str, object]],
    *,
    shortlist_limit: int,
    heuristics: HeuristicConfig,
) -> list[dict[str, object]]:
    if len(raw_markets) <= shortlist_limit:
        return raw_markets

    pinned_tickers = set(heuristics.validation_market_tickers)
    ranked = sorted(raw_markets, key=lambda market: score_prefetch_candidate(market, heuristics), reverse=True)
    shortlisted: list[dict[str, object]] = []
    seen_tickers: set[str] = set()

    for market in raw_markets:
        ticker = str(market.get("ticker", ""))
        if ticker in pinned_tickers and ticker not in seen_tickers:
            shortlisted.append(market)
            seen_tickers.add(ticker)

    for market in ranked:
        ticker = str(market.get("ticker", ""))
        if ticker and ticker not in seen_tickers:
            shortlisted.append(market)
            seen_tickers.add(ticker)
        if len(shortlisted) >= shortlist_limit:
            break

    return shortlisted


def _history_shortlist_limit(limit: int, heuristics: HeuristicConfig) -> int:
    shortlist_multiplier = max(1, (heuristics.selection_candidate_pool_multiplier + 1) // 2)
    return max(limit, limit * shortlist_multiplier)


def _build_candidate_contexts(
    raw_markets: list[dict[str, object]],
    *,
    pool: str,
    limit: int,
    client: KalshiClient,
    settings: Settings,
    heuristics: HeuristicConfig,
) -> list[MarketCandidateContext]:
    shortlisted = _shortlist_raw_markets(
        raw_markets,
        shortlist_limit=_history_shortlist_limit(limit, heuristics),
        heuristics=heuristics,
    )
    return [
        build_candidate_context(
            raw_market=market,
            pool=pool,
            client=client,
            settings=settings,
            heuristics=heuristics,
        )
        for market in shortlisted
    ]


def _load_selected_candidate_contexts(heuristics: HeuristicConfig) -> list[MarketCandidateContext]:
    settings = _settings()
    client = _kalshi_client()

    open_raw = client.list_markets(
        limit=max(heuristics.tracked_market_limit * heuristics.selection_candidate_pool_multiplier, 20),
        status="open",
    )
    historical_raw = client.list_historical_markets(
        limit=max(heuristics.historical_market_limit * heuristics.selection_candidate_pool_multiplier, 12)
    )

    open_contexts = _build_candidate_contexts(
        open_raw,
        pool="open",
        limit=heuristics.tracked_market_limit,
        client=client,
        settings=settings,
        heuristics=heuristics,
    )
    historical_contexts = _build_candidate_contexts(
        historical_raw,
        pool="historical",
        limit=heuristics.historical_market_limit,
        client=client,
        settings=settings,
        heuristics=heuristics,
    )

    _ranked_open, selected_open = rank_candidate_contexts(
        open_contexts,
        limit=heuristics.tracked_market_limit,
        validation_market_tickers=heuristics.validation_market_tickers,
    )
    _ranked_historical, selected_historical = rank_candidate_contexts(
        historical_contexts,
        limit=heuristics.historical_market_limit,
        validation_market_tickers=heuristics.validation_market_tickers,
    )
    return selected_open + selected_historical


def _load_ranked_candidate_contexts(heuristics: HeuristicConfig) -> list[MarketCandidateContext]:
    settings = _settings()
    client = _kalshi_client()
    open_raw = client.list_markets(
        limit=max(heuristics.tracked_market_limit * heuristics.selection_candidate_pool_multiplier, 20),
        status="open",
    )
    historical_raw = client.list_historical_markets(
        limit=max(heuristics.historical_market_limit * heuristics.selection_candidate_pool_multiplier, 12)
    )
    contexts = _build_candidate_contexts(
        open_raw,
        pool="open",
        limit=heuristics.tracked_market_limit,
        client=client,
        settings=settings,
        heuristics=heuristics,
    ) + _build_candidate_contexts(
        historical_raw,
        pool="historical",
        limit=heuristics.historical_market_limit,
        client=client,
        settings=settings,
        heuristics=heuristics,
    )
    ranked, _selected = rank_candidate_contexts(
        contexts,
        limit=heuristics.tracked_market_limit + heuristics.historical_market_limit,
        validation_market_tickers=heuristics.validation_market_tickers,
    )
    return ranked


def _load_market_context_by_id(
    market_id: str,
    heuristics: HeuristicConfig,
) -> MarketCandidateContext | None:
    settings = _settings()
    client = _kalshi_client()
    raw_market = client.get_market(market_id)
    pool = "open"
    if raw_market is None:
        raw_market = client.get_historical_market(market_id)
        pool = "historical"
    if raw_market is None:
        return None
    return build_candidate_context(
        raw_market=raw_market,
        pool=pool,
        client=client,
        settings=settings,
        heuristics=heuristics,
    )


def _market_row(
    *,
    context: MarketCandidateContext,
    last_event_at: str | None,
    event_count: int,
) -> dict[str, object]:
    normalized_market = context.normalized_market
    return {
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
        "event_count": event_count,
        "last_event_at": last_event_at,
        "detail_url": normalized_market.detail_url,
        "rules_primary": normalized_market.rules_primary,
        "rules_secondary": normalized_market.rules_secondary,
        "metadata": _json(
            {
                **normalized_market.metadata,
                "selection_debug": context.selection_debug.model_dump(),
                "market_quality": context.quality_summary.model_dump(),
                "pool": context.pool,
            }
        ),
    }
