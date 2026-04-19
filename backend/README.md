# Prediction Market Assistant Backend

FastAPI backend for the frontend market contract used during the Prediction Hunt plumbing stage.

## Current Direction

`Prediction Hunt` is the only active provider integration in this stage.

The backend currently does three things:

1. fetches active market rows from Prediction Hunt
2. maps them into the app's existing `MarketSummary` and `MarketDetail` contract
3. derives a lightweight synthetic recent-move event from Prediction Hunt price history when enough candles are available

This is intentionally a plumbing-first setup. It is not the final event-detection or enrichment architecture.

## Endpoints

- `GET /api/health`
- `GET /api/dashboard`
- `GET /api/markets`
- `GET /api/markets/{market_id}`
- `GET /api/markets/{market_id}/events`
- `GET /api/internal/providers/prediction-hunt/status`
- `GET /api/internal/providers/prediction-hunt/events`
- `GET /api/internal/providers/prediction-hunt/markets`
- `GET /api/internal/providers/prediction-hunt/matching-markets`
- `GET /api/internal/providers/prediction-hunt/prices/history`
- `GET /api/internal/providers/prediction-hunt/orderbook`
- `GET /api/internal/providers/prediction-hunt/desk`

## Architecture

- `backend/app/api/routes.py` keeps the route layer thin
- `backend/app/services/markets.py` owns the core app-facing market mapping
- `backend/app/services/prediction_hunt.py` owns provider calls, throttling, caching, and response parsing
- `backend/app/models/market.py` remains the frontend/backend contract boundary

## Logging

This plumbing stage includes lightweight logging for:

- core route entry points
- Prediction Hunt market-load success and fallback
- mapping failures
- event-history skips and fallbacks
- upstream Prediction Hunt HTTP errors

The goal is local debugging visibility, not full observability.

## Fallback Behavior

If Prediction Hunt is unavailable or not configured, the backend falls back to the existing mock market data for the core app routes. This keeps the UI usable while the plumbing is being tightened.

## Environment

See `backend/.env.example`.

Current variables:

- `BACKEND_CORS_ORIGINS`
- `PREDICTION_HUNT_API_URL`
- `PREDICTION_HUNT_API_KEY`
- `PREDICTION_HUNT_MIN_INTERVAL_SECONDS`

## Local Dev

```bash
uv sync
uv run uvicorn app.main:app --reload
```

`uv sync` now installs the backend dev toolchain by default through `uv` dependency groups. If you ever want a lean runtime-only environment, use `uv sync --no-dev`.

## Testing

```bash
uv run python -m pytest
```