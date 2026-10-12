# Tasks

## 1. Core evidence

- [x] 1.1 Add a `Facet(trip_id, label, vector)` model and make `rank_destinations` accept facets-or-vectors, recording the strongest facet's trip and similarity; verify a test asserts the closest trip is captured, and that bare-vector callers still work.
- [x] 1.2 Split attribute matching into `matched_attributes(...)` returning a weight map while keeping `attribute_score` as its sum; verify tests pin the score and the matched keys.
- [x] 1.3 Add `nearest_visited_km(...)`; verify a test returns the closest center's distance.
- [x] 1.4 Extend `Recommendation` with `best_trip_id`, `best_trip_label`, `best_facet_similarity`, `matched_attributes`, `nearest_trip_km`; verify ranking populates them.

## 2. Persistence

- [x] 2.1 Add the new recommendation columns and the `recommendation_explanations` cache table via `db._migrate`; verify `tests/test_db.py` covers fresh and legacy databases.
- [x] 2.2 Persist the evidence in `run_recommend`; verify `tests/test_recommend.py` reads back the matched attributes and closest trip.

## 3. Deterministic explanation

- [x] 3.1 Rewrite `explain` to build evidence-based prose (closest trip, recurring attributes, novelty) with a short generic fallback; verify unit tests for each branch.
- [x] 3.2 Wire it in `run_recommend` so every Recommendation gets the richer explanation by default; verify a test asserts the explanation names the trip and an attribute.
- [x] 3.3 Verify ranking order is unchanged by the evidence work; verify a test compares ordering before/after.

## 4. Optional LLM synthesis

- [x] 4.1 Add the `ExplanationSynthesizer` port and a default implementation under `models/` with a pinned model and prompt version; verify the model runtime stays confined to `models/` (existing confinement test).
- [x] 4.2 Cache synthesis by evidence hash in `recommendation_explanations` and reuse it; verify a test asserts a second run reuses the cached text without calling the model.
- [x] 4.3 Make synthesis non-fatal and opt-in; verify a test with a raising synthesizer still returns recommendations with the deterministic text.

## 5. Web evidence

- [x] 5.1 Add matched attributes and the closest trip to the destination view model; verify `tests/test_web_views.py` covers present and absent evidence.
- [x] 5.2 Show shared-attribute chips and a "closest to your …" line on the destination page; verify `TestClient` renders them and omits them when absent.

## 6. Documentation and integration

- [x] 6.1 Update `README.md`/`AGENTS.md` for the richer explanation and the optional synthesis flag; verify the documented command runs.
- [x] 6.2 Walk ranking → persistence → destination page with evidence and no network; verify every page is 200 and `.venv/bin/python -m pytest -q` is green.

## Workflow follow-up

- Resume the paused `destination-guide` change after this one is applied.
- Archive the change once review is satisfied and the specs are synced.
