# Prediction Market Assistant Backend

Backend service for the Phase 3 market and event contract.

This backend is no longer just a thin FastAPI scaffold. It now includes a first-pass hosted backend architecture that:

- syncs markets and history from Kalshi over REST
- normalizes provider data into backend-owned contracts
- persists canonical operational data in Supabase Postgres
- stores raw artifacts in Amazon S3
- runs deterministic event detection on normalized history
- attaches bounded source-backed signals before returning `MarketEvent` data

The route surface is intentionally unchanged while the service layer underneath it has been replaced.

## Endpoints

- `GET /api/health`
- `GET /api/dashboard`
- `GET /api/markets`
- `GET /api/markets/{market_id}`
- `GET /api/markets/{market_id}/events`
- `GET /api/internal/heuristics/markets`
- `GET /api/internal/heuristics/markets/{market_id}/evaluate`

## Current Architecture

The current backend flow is:

1. `Kalshi REST` is treated as the canonical upstream for market metadata and candlestick history.
2. `backend/app/services/kalshi/` normalizes Kalshi responses into provider-agnostic market and history shapes.
3. `backend/app/services/events/` runs deterministic event-window detection on normalized history.
4. `backend/app/services/signals/` attaches bounded signals and source-document records to detected windows.
5. `backend/app/services/persistence.py` persists markets, history, events, signals, source docs, artifacts, and research runs into Supabase Postgres.
6. `backend/app/services/artifacts.py` stores raw market metadata and candlestick payloads in S3.
7. `backend/app/services/markets.py` orchestrates the sync pipeline and serves the existing route contract.

## Key Technical Decisions

### Source Of Truth

- `Supabase Postgres` is the canonical operational store.
- `Amazon S3` is used for raw artifacts and replayable payload retention.
- `Kalshi` remains the upstream market-data source, not the product-facing system of record.
- The API routes continue to read from backend services, not directly from provider payloads.

### Route Contract Preservation

The existing frontend/backend contract in `frontend/lib/market-types.ts` and `backend/app/models/market.py` was preserved.

- routes remain thin in `backend/app/api/routes.py`
- orchestration lives in `backend/app/services/markets.py`
- the frontend repository boundary stays intact

### Sync Strategy

The first implementation intentionally uses `REST + polling` only.

- No websocket ingestion is required for the current runtime.
- Sync is triggered lazily through service reads and throttled by `SYNC_INTERVAL_SECONDS`.
- Websockets are deferred until the REST-based flow is stable and producing good events.

### Market Selection Strategy

The current tracked-market selection is now quality-aware instead of pure volume ranking.

The sync and evaluation paths both:

- fetch a broader candidate pool for open and historical markets
- normalize history before deciding which markets deserve the limited rollout slots
- score each candidate using a weighted blend of:
  - raw market activity (`volume_fp`, `open_interest_fp`)
  - non-zero price fields
  - normalized history density
  - non-zero probability ratio
  - recent movement across the retrieved history window
- penalize markets with all-zero price fields, synthetic-only history, or weak detector input
- keep the top `TRACKED_MARKET_LIMIT` open markets and top `HISTORICAL_MARKET_LIMIT` historical markets
- surface selection-debug metadata so the internal evaluator can explain why a market was or was not selected

Current defaults:

- `TRACKED_MARKET_LIMIT=12`
- `HISTORICAL_MARKET_LIMIT=6`
- `VALIDATION_MARKET_TICKERS=` optional comma-separated repeatable validation set

Important note:

- This is still a heuristic rollout strategy, not a final ranking model.
- The internal heuristics playground is the intended place to iterate on these weights and thresholds without touching the user-facing route contract.

### History Shape

The detector input was intentionally kept minimal:

- `timestamp`
- `probability`

Additional fields are preserved when available:

- `yes_bid`
- `yes_ask`
- `volume`
- `open_interest`
- `source`
- `metadata`

This keeps the event detector stable while still preserving richer provider context for later improvements.

### Event Detection Heuristic

The current detector in `backend/app/services/events/detector.py` is deterministic and explainable.

It currently:

- builds raw candidates from each anchor point
- records candidate-level debug payloads before filtering
- applies threshold, cooldown, merge, and cap filters explicitly
- returns filtered-candidate drop reasons for internal evaluation
- keeps the final user-facing event surface deterministic and stable

Current defaults:

- `EVENT_THRESHOLD=0.05`
- `EVENT_COOLDOWN_POINTS=2`
- `MAX_EVENTS_PER_MARKET=4`

### Event Identity And Idempotency

The current implementation explicitly bakes in logical-event identity.

- event IDs are derived from `market_id + start_time + end_time + detector_version`
- a separate revision hash is generated from the event payload
- time-series rows are keyed by `(market_id, timestamp)`
- markets are upserted by ID
- market events are replaced per market on each sync

This is a practical first-pass idempotency strategy for repeated polling-based recomputation.

### Signal Retrieval Strategy

Signal attachment is intentionally narrow in V1.

Current signal sources are backend-generated and deterministic:

- a Kalshi rules-derived document
- a Kalshi market snapshot derived from normalized history near the event window

Routing is also deterministic:

- `< 0.03` move: `skip`
- `< 0.08` move: `light_research`
- `>= 0.08` move: `deep_research`

Current default bound:

- `MAX_SIGNALS_PER_EVENT=12`

This is scaffolding for later expansion into external source retrieval. The persistence model already stores source documents and signal rows so we can evolve the retrieval layer without changing the core schema shape again.

### Internal Evaluation Path

There is now a separate read-only evaluation surface for heuristic work.

- It reuses the live Kalshi -> normalize -> detect -> signal pipeline for a single market.
- It does not persist markets, events, artifacts, or research runs.
- Request-scoped overrides are applied to a temporary heuristic config only.
- The payload includes:
  - market quality summary
  - selection scoring/debug info
  - raw candidates
  - filtered candidates with drop reasons
  - final events
  - routing decisions
  - signal candidates before and after trimming

### Mock Fallback Behavior

The backend still has a fixture fallback path.

- If runtime persistence/service access fails, service methods fall back to `backend/app/data/mock_markets.py`.
- This keeps the route contract alive during early backend iteration.
- The goal is to remove reliance on that fallback as the real pipeline matures.

## Persistence Model

The current Postgres schema is created at runtime in `backend/app/services/persistence.py`.

Tables created today:

- `markets`
- `market_time_series`
- `market_events`
- `artifacts`
- `source_documents`
- `signal_records`
- `research_runs`

These correspond to the main architectural decisions from the plan:

- normalized markets and history live in Postgres
- event windows and signal attachments live in Postgres
- raw artifacts are referenced from Postgres and stored in S3
- research routing decisions are logged in Postgres

## Files Added Or Changed

Major additions:

- `backend/app/config.py`
- `backend/app/services/artifacts.py`
- `backend/app/services/persistence.py`
- `backend/app/services/kalshi/client.py`
- `backend/app/services/kalshi/normalize.py`
- `backend/app/services/kalshi/types.py`
- `backend/app/services/events/detector.py`
- `backend/app/services/events/types.py`
- `backend/app/services/signals/provider.py`
- `backend/app/services/signals/scoring.py`
- `backend/app/services/signals/attach.py`
- `backend/tests/test_event_detector.py`
- `backend/tests/test_kalshi_normalize.py`

Updated core files:

- `backend/app/main.py`
- `backend/app/services/markets.py`
- `backend/.env.example`
- `backend/pyproject.toml`

## Local Dev

1. Install dependencies and sync the local environment: `uv sync`
2. Run the backend: `uv run uvicorn app.main:app --reload`

`uv run` uses the project virtualenv automatically.

## Environment

The backend now expects these environment variables:

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
- `KALSHI_API_KEY` or `KALSHI_API_KEY_ID`
- `KALSHI_API_BASE_URL`
- `KALSHI_PRIVATE_KEY_PATH`
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

## Verification

What has been verified in the current implementation:

- Supabase HTTP/API credentials work
- Supabase pooled DB connection works
- S3 credentials and bucket access work
- Kalshi authenticated API access works
- backend unit tests for normalization and event detection pass
- live backend ingestion can pull markets and populate the dashboard market list

## Current Caveats

The biggest current caveat is not infrastructure, it is product/runtime quality:

- the production Kalshi pipeline is syncing markets successfully
- the initial tracked subset is still producing `0` detected top events
- many selected markets currently have flat or zero-valued price fields in the first-pass selection

That means the next backend iteration should likely focus on:

- improving market selection quality
- choosing markets with useful non-zero history
- refining the event detector against real synced series
- deciding whether fallback probability logic should be stronger when trade prices are sparse

## Testing

Run tests with:

```bash
uv run --extra dev pytest
```

Current tests cover:

- Kalshi market normalization
- Kalshi candlestick normalization
- deterministic event detection

## Phase Gates

Phase readiness notes for backend-heavy work and future canvas mode live in `docs/phase-gates.md`.