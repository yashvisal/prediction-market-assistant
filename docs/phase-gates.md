# Phase Gates

## Backend-Heavy Phase 4 Gate

Only start deeper ingestion, event detection, signal retrieval, and AI orchestration work when all of these are true:

- `frontend/lib/market-types.ts` and `backend/app/models/market.py` describe the same intentional contract.
- Route files read through `frontend/lib/repositories/markets.ts` instead of importing fixtures directly.
- Shared derivations live in `frontend/lib/domain/` or `backend/app/services/`, not in UI components or route files.
- Backend routes stay thin and backend-owned aggregation lives in `backend/app/services/`.
- One fixture story exists for transition work: frontend fixture helpers under `frontend/lib/fixtures/` and temporary backend seed data under `backend/app/data/`.
- The dashboard snapshot is backend-owned when the API is enabled, so the frontend does not fan out to fetch every market's events to build the home view.
- Existing route boundaries remain intact: loading, error, and not-found states continue to work while data sources change.

## Canvas Gate

Only begin canvas mode when all of these are true:

- The market workspace is trusted on real backend-driven data.
- Graph nodes and edges derive from the same `MarketEvent`, `Signal`, `Entity`, and related-event contract already used by the market page.
- No canvas-only DTO layer or duplicated graph-specific domain model has been introduced.
- Any canvas mapping logic lives in a dedicated domain layer and treats the market page as the source of truth, not a competing workflow.
