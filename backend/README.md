# Topic Intelligence Backend

FastAPI backend for a topic-centric intelligence system built on top of Prediction Hunt signals.

## Current Direction

`Prediction Hunt` is the primary signal provider in the current architecture.

The backend currently focuses on three layers:

1. provider access and normalization through `Prediction Hunt`
2. cheap signal-layer derivation from provider markets and price history
3. topic assembly that produces canonical `Topic State` for downstream layers

This repo is intentionally in a cleanup plus Phase 1 state. Topic explanation, digest generation, and broader enrichment come later.

## Active Product Contract

Forward-looking product routes:

- `GET /api/health`
- `GET /api/topics`
- `GET /api/topics/{topic_id}`

Internal provider/debug routes:

- `GET /api/internal/providers/prediction-hunt/status`
- `GET /api/internal/providers/prediction-hunt/events`
- `GET /api/internal/providers/prediction-hunt/markets`
- `GET /api/internal/providers/prediction-hunt/matching-markets`
- `GET /api/internal/providers/prediction-hunt/prices/history`
- `GET /api/internal/providers/prediction-hunt/orderbook`
- `GET /api/internal/providers/prediction-hunt/desk`

Legacy compatibility routes may still exist temporarily during cleanup, but they are not the forward-looking product contract.

## Architecture

- `backend/app/api/routes.py` keeps the route layer thin
- `backend/app/services/prediction_hunt.py` owns provider calls, throttling, caching, and response parsing
- `backend/app/services/markets.py` remains a temporary internal signal-layer adapter over provider market data
- `backend/app/services/topics.py` assembles canonical `Topic State`
- `backend/app/models/topic.py` defines the topic-facing contract
- shared signal/evidence primitives live in `backend/app/models/intelligence.py`

## Environment

See `backend/.env.example`.

Current variables:

- `BACKEND_CORS_ORIGINS`
- `PREDICTION_HUNT_API_URL`
- `PREDICTION_HUNT_API_KEY`
- `PREDICTION_HUNT_MIN_INTERVAL_SECONDS`
- `TOPIC_STATE_CACHE_TTL_SECONDS`

## Local Dev

```bash
uv sync
uv run uvicorn app.main:app --reload
```

## Testing

```bash
uv run python -m pytest
```

