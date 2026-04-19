# Prediction Market Assistant Frontend

Next.js app for the dashboard, market gallery, and market workspace.

## Current Data Story

During the plumbing stage, the frontend reads its core data from the backend market contract:

- `GET /api/dashboard`
- `GET /api/markets`
- `GET /api/markets/{market_id}`
- `GET /api/markets/{market_id}/events`

The only active provider-specific internal surface is the Prediction Hunt desk:

- `frontend/app/(main)/(internal)/providers/prediction-hunt/page.tsx`

## Environment

Create `frontend/.env.local` with:

```bash
PREDICTION_MARKET_API_BASE_URL=http://localhost:8000
```

## Local Dev

```bash
pnpm install
pnpm dev
```
