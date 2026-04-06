# Prediction Market Assistant Backend

Minimal FastAPI scaffold for the Phase 3 contract.

## Endpoints

- `GET /api/health`
- `GET /api/dashboard`
- `GET /api/markets`
- `GET /api/markets/{market_id}`
- `GET /api/markets/{market_id}/events`

## Local Dev

1. Install dependencies (creates/updates `.venv` and `uv.lock`): `uv sync`
2. Run the server: `uv run uvicorn app.main:app --reload`

`uv run` uses the project’s virtual environment so you do not need to activate it manually.

## Environment

- `BACKEND_CORS_ORIGINS` comma-separated list of allowed origins

## Phase Gates

Phase readiness notes for backend-heavy work and future canvas mode live in `docs/phase-gates.md`.
