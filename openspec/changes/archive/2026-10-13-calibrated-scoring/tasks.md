# Tasks

## 1. Calibration

- [x] 1.1 Separate `base` and `delta` in the scoring loop (vector stays last) and add `_calibrate` (min-max rescale of embedding/attribute per pool) behind `calibrate=False`; verify tests for normalized scores, order preservation, and off-by-default equivalence.
- [x] 1.2 Wire `calibrate` through `config`, the recommend pipeline, and `recommend --calibrate`; verify config and CLI parsing.

## 2. Exact-title pageviews

- [x] 2.1 Add `article_title` and use it in `fetch_popularity_for`; verify a test that a `wv:` id uses its title and a titleless id falls back to the name.

## 3. Documentation and verification

- [x] 3.1 Update `README.md` for `--calibrate`; verify the documented command runs.
- [x] 3.2 Run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
