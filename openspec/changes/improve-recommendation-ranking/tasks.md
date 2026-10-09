# Tasks

## 1. Scoring core

- [x] 1.1 Add `taste_attribute_weights(tags)` and `destination_attribute_set(destination)` using the shared vocabulary. Verify: unit tests canonicalize sample tags and descriptions.
- [x] 1.2 Combine embedding and attribute scores in `rank_destinations` (configurable `alpha`), recording `embedding_score` and `attribute_score` on each Recommendation. Verify: a test ranks a coastal candidate above an inland one with similar embeddings; a repeatability test passes.

## 2. Pipeline wiring

- [x] 2.1 Pass the profile's attribute weights into `run_recommend` and `run_eval`. Verify: a test with a coastal profile ranks a coastal catalog entry first.

## 3. Integration & docs

- [x] 3.1 Re-run `recommend --count 5` on the Malta archive; verify coastal cities outrank inland ones (Rivas-Vaciamadrid drops) and scores now spread.
- [x] 3.2 Re-run `eval` (hold-out Malta) and update `docs/ROADMAP.md` with the result.
