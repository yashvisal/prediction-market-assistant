# Prediction Market Assistant Backend

FastAPI backend for the market, event, and heuristics contracts used by the app.

The active provider path is now Dome for Polymarket. The backend treats Dome as the deterministic first layer that discovers events and markets, hydrates useful history, runs explainable event detection, and attaches bounded provider-backed signals before any later LLM research.

## Endpoints

- `GET /api/health`
- `GET /api/dashboard`
- `GET /api/markets`
- `GET /api/markets/{market_id}`
- `GET /api/markets/{market_id}/events`
- `GET /api/internal/heuristics/markets`
- `GET /api/internal/heuristics/markets/{market_id}/evaluate`
- `GET /api/internal/dome/polymarket/markets`
- `GET /api/internal/dome/polymarket/events`
- `GET /api/internal/dome/polymarket/discovery`
- `GET /api/internal/dome/polymarket/markets/{market_slug}`

## Current Architecture

The current backend flow is:

1. `Dome Polymarket REST` is the canonical upstream for event discovery, market metadata, price history, trades, orderbook snapshots, and candlesticks.
2. `backend/app/services/dome_markets.py` handles provider access, rate-limit-aware caching, event/market hydration, and raw evidence collection.
3. `backend/app/services/dome_normalize.py` converts Dome payloads into provider-neutral market and history shapes.
4. `backend/app/services/market_analysis.py` scores discovery candidates and evaluates single-market heuristic runs.
5. `backend/app/services/events/` turns normalized history into deterministic event windows.
6. `backend/app/services/signals/` attaches bounded provider-backed context documents and routing decisions.
7. `backend/app/services/persistence.py` persists markets, history, events, signals, source docs, artifacts, and research runs into Supabase Postgres.
8. `backend/app/services/artifacts.py` stores replayable raw artifacts in S3.

## Key Technical Decisions

### Source Of Truth

- `Supabase Postgres` is the canonical operational store.
- `Amazon S3` stores raw artifacts and replayable upstream payloads.
- `Dome` is the active upstream provider, not the product-facing system of record.
- API routes continue to read from backend services, not directly from provider responses.

### Route Contract Preservation

The existing frontend/backend contract in `frontend/lib/market-types.ts` and `backend/app/models/market.py` remains stable.

- routes stay thin in `backend/app/api/routes.py`
- orchestration lives in `backend/app/services/markets.py`
- provider-specific logic stays out of the API layer

### Event-First Discovery

Raw contracts are no longer the only discovery primitive.

The backend now:

- fetches open and closed Dome events with their child markets
- derives lightweight prefetch scores before doing heavier history hydration
- ranks candidate markets using event and market evidence rather than raw recency alone
- exposes event shortlist metadata in the heuristics surface so tuning can focus on useful daily discovery

Current shortlist inputs include:

- market volume and weekly activity
- event-level volume
- title specificity / interpretability
- history coverage
- recent trade presence
- orderbook presence
- spread penalties

This is still a heuristic ranking system, not a learned model.

### History Model

The detector input remains intentionally simple:

- `timestamp`
- `probability`

Additional context is preserved when available:

- `yes_bid`
- `yes_ask`
- `volume`
- `open_interest`
- `source`
- `metadata`

For Dome-backed markets, the backend prefers candlesticks. If candlesticks are missing or sparse, it falls back to sampled historical prices and marks the source accordingly.

### Event Detection

`backend/app/services/events/detector.py` is still deterministic and explainable.

It:

- builds raw candidates from history anchors
- applies threshold, cooldown, merge, and cap filters
- exposes drop reasons in the internal evaluator
- keeps final event windows stable and reproducible

Defaults:

- `EVENT_THRESHOLD=0.05`
- `EVENT_COOLDOWN_POINTS=2`
- `MAX_EVENTS_PER_MARKET=4`

### Signal Attachment

Signal attachment is intentionally narrow in V1.

The current provider-backed signals are:

- a provider-derived market context document
- a market snapshot near the detected event window

Routing stays deterministic:

- `< 0.03` move: `skip`
- `< 0.08` move: `light_research`
- `>= 0.08` move: `deep_research`

This remains the deterministic layer before broader external retrieval or LLM research.

### Internal Heuristics Evaluation

There is a dedicated read-only evaluation surface for tuning.

It:

- reuses the live Dome -> normalize -> detect -> signal pipeline for a single market
- does not persist markets, events, artifacts, or research runs
- applies heuristic overrides on the request only
- returns:
  - discovery/event shortlist context
  - market quality summary
  - selection scoring/debug info
  - raw candidates
  - filtered candidates with drop reasons
  - final events
  - routing decisions
  - signal candidates before and after trimming

### Rate-Limit Strategy

Rate limits are treated as a first-class runtime constraint.

The Dome client now:

- caches recent GET responses in memory with endpoint-specific TTLs
- serves cached responses when possible
- falls back to stale cached payloads on `429` for non-critical reads
- degrades detail views to partial evidence instead of failing entirely

This keeps the internal tuning loop responsive and avoids repeating the Kalshi bottleneck.

### Idempotency

The current implementation keeps logical-event identity stable:

- event IDs derive from `market_id + start_time + end_time + detector_version`
- event revisions use a payload hash
- time-series rows are keyed by `(market_id, timestamp)`
- market events are replaced per market on sync

## Persistence Model

Runtime schema lives in `backend/app/services/persistence.py`.

Tables:

- `markets`
- `market_time_series`
- `market_events`
- `artifacts`
- `source_documents`
- `signal_records`
- `research_runs`

These store normalized operational state, not raw provider objects directly.

## Local Dev

1. Install dependencies: `uv sync`
2. Run the backend: `uv run uvicorn app.main:app --reload`

`uv run` uses the project virtualenv automatically.

## Environment

Required environment variables:

- `BACKEND_CORS_ORIGINS`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_PUBLISHABLE_KEY` or `SUPABASE_ANON_KEY`
- `SUPABASE_DB_URL`
- `AWS_REGION`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `S3_BUCKET`
- `S3_PREFIX`
- `DOME_API_BASE_URL`
- `DOME_API_KEY`
- `TRACKED_MARKET_LIMIT`
- `HISTORICAL_MARKET_LIMIT`
- `SYNC_INTERVAL_SECONDS`
- `HISTORY_WINDOW_DAYS`
- `EVENT_THRESHOLD`
- `EVENT_COOLDOWN_POINTS`
- `MAX_EVENTS_PER_MARKET`
- `MAX_SIGNALS_PER_EVENT`
- `VALIDATION_MARKET_TICKERS`
- `PERSISTENCE_ENABLED`

See `backend/.env.example` for a template.

## Testing

Run tests with:

```bash
uv run --extra dev pytest
```

Focused checks used during this migration included:

- Dome parsing and quality-summary tests
- deterministic event detection tests
- market-selection debug tests
- heuristics shortlist tests

## Current Caveats

The main remaining risks are now product-quality questions rather than provider viability:

- event-first discovery still needs more tuning around vague child-contract titles
- the heuristics shortlist should keep improving its notion of market usefulness for downstream research
- signal attachment is still provider-backed scaffolding, not full external evidence retrieval

## Phase Gates

Phase readiness notes for backend-heavy work and future canvas mode live in `docs/phase-gates.md`.