# Tasks

- [x] 1.1 Add recency weighting to `load_taste_facets` behind a configurable half-life (off by default); verify a test that an old trip is down-weighted and the default is unchanged.
- [x] 1.2 Add an `anti_match_weight` term to `rank_destinations` (capped, off by default); verify tests that a generic-only match is penalised and the default is unchanged.
- [x] 1.3 Make the candidate pre-filter configurable and wire `recency_half_life_days`, `anti_match_weight`, and `candidate_prefilter` through config and the CLI; verify parsing.
- [x] 1.4 Update `README.md`; run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
