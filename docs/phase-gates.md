# Phase Gates

## Topic Foundation Gate

Only move beyond cleanup plus Phase 1 when all of these are true:

- `backend/app/models/topic.py` and `frontend/lib/topic-types.ts` describe the same intentional topic contract.
- `Topic State` is the canonical downstream system state produced by topic assembly.
- route files read through `frontend/lib/repositories/topics.ts` for forward-looking topic surfaces.
- shared derivations live in `frontend/lib/domain/` or `backend/app/services/`, not in UI components or route files.
- backend routes stay thin and backend-owned aggregation lives in `backend/app/services/`.
- one fixture story exists for topic transition work under `frontend/lib/fixtures/` and temporary backend seed data under `backend/app/data/`.
- topic assembly remains cheap, continuous, and largely free of LLM-based logic.
- existing loading, error, and not-found states continue to work while topic routes replace market-first surfaces.

## Intelligence Gate

Only begin explanation, digest generation, signal retrieval expansion, or AI orchestration when all of these are true:

- Topic State has been validated as a stable and useful foundation.
- topic routes and topic repository seams are stable enough that new intelligence layers do not have to depend on legacy market pages.
- explanation and digest layers consume Topic State instead of recomputing their own parallel topic grouping.
- deterministic signal-layer logic remains separate from LangChain-based intelligence workflows.

## Future Visualization Gate

Only begin timeline or canvas-like exploration work when all of these are true:

- topic detail views are trusted on real backend-driven topic data.
- graph or timeline nodes derive from the same shared signal, entity, and topic-update primitives already used by the topic experience.
- no visualization-only DTO layer or duplicated graph-specific domain model has been introduced.
- any visualization mapping logic lives in a dedicated domain layer and treats topic state as the source of truth, not a competing workflow.