# Tasks

- [x] 1.1 Add `feedback.reason` (with a migration) and capture it in the CLI and web; verify a test that a reason is stored.
- [x] 1.2 Derive a deterministic learned bias vector (mean liked − mean disliked destination embeddings) and apply it in ranking behind an off-by-default weight; verify tests for the bias and its deterministic reuse.
- [x] 1.3 Version runs: increment `run_id`, keep history (bounded), log impressions, and have readers use the latest run; verify tests for run history and impressions.
- [x] 1.4 Show reason chips and a "new since last run" badge; verify a render and `test_web`/`test_web_views` pass.
- [x] 1.5 Update `README.md`; run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
