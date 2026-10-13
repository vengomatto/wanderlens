# Tasks

## 1. Diversity (MMR)

- [x] 1.1 Add MMR selection to `rank_destinations` with a `diversity` weight, keeping `diversity=0` equal to the previous order; verify a test where near-duplicates are pushed apart and a test that `diversity=0` matches the old ranking.
- [x] 1.2 Verify determinism: ranking twice with the same inputs and weight yields the identical list.

## 2. Popularity source

- [x] 2.1 Add `catalog/popularity.py`: fetch Wikimedia pageviews for a Destination, normalize to a score, classify famous/balanced/uncommon; verify tests with a fake session cover a hit, a miss, and classification thresholds.
- [x] 2.2 Add the catalog-scoped `destination_popularity` table and negative caching; verify tests avoid a refetch.

## 3. Ranking integration

- [x] 3.1 Accept a `novelty` preference that biases scores by popularity before MMR; verify tests for familiar, uncommon, and balanced.
- [x] 3.2 Fetch popularity for the recommended Destinations best-effort in `run_recommend`, persist `popularity`/`popularity_label`, and add `--diversity`/`--novelty` flags; verify a test with an injected fake fetcher and CLI parsing.
- [x] 3.3 Verify a popularity-source error never fails `run_recommend`.

## 4. Web

- [x] 4.1 Carry popularity on the recommendation and destination view models; verify `tests/test_web_views.py`.
- [x] 4.2 Show the famous/balanced/uncommon label on the card and destination page; verify `TestClient` renders it and omits it when absent.

## 5. Documentation and verification

- [x] 5.1 Update `README.md`/`AGENTS.md` for `--diversity`/`--novelty`; verify the documented command runs.
- [x] 5.2 Run `.venv/bin/python -m pytest -q`; verify it is green.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
