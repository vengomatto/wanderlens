# Tasks

- [x] 1.1 Add `models/profiles.py` `HostedProfileWriter` with a pinned prompt and a `_parse` that validates types/ranges and drops unknown fields; verify tests for valid and invalid output.
- [x] 1.2 Add `catalog/profiles.py` with a keyless baseline (vibe from attributes), a model merge that marks estimated fields, and a catalog-scoped `destination_profiles` cache; verify tests for the baseline, the merge, validation fallback, and cache reuse.
- [x] 1.3 Wire it into `run_recommend` (opt-in, best-effort) plus `config.build_profiles` and `recommend --profiles`; verify config and CLI parsing.
- [x] 1.4 Show vibe chips and suitability fields (estimated marked) on the destination page; verify a `TestClient` render shows them and omits the section when absent.
- [x] 1.5 Update `README.md`; run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
