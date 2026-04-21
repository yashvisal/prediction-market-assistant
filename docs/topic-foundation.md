# Topic Foundation

This document captures the preparation-phase decisions that support the first topic-centric implementation slice.

## Legacy Contract

The existing market surfaces remain supported as legacy plumbing:

- `GET /api/dashboard`
- `GET /api/markets`
- `GET /api/markets/{market_id}`
- `GET /api/markets/{market_id}/events`

They should not be extended to carry topic/feed concepts.

## New Phase 1 Seams

Phase 1 introduces a parallel topic contract:

- `GET /api/topics`
- `GET /api/topics/{topic_id}`

Backend topic logic lives under `backend/app/services/topics.py`.
Frontend topic access lives under `frontend/lib/repositories/topics.ts`.

Topic assembly produces `Topic State`, and `Topic State` is the canonical system state consumed by all downstream layers.

## Runtime Foundation

Phase 1 topic state is intentionally lightweight:

- topic assembly reuses the existing market/event service layer
- topic state is cached in-process using `TOPIC_STATE_CACHE_TTL_SECONDS`
- no durable topic store or scheduler is introduced yet
- no explanation or digest artifact pipeline is introduced yet

This is a temporary foundation for validating topic contracts and seeded topic assembly before moving to explanation and digest phases.
