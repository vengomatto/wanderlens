# Tasks

- [x] 1.1 Harden the re-ranker path in `run_recommend` so a `ranker` error falls back to deterministic explanations; verify a test.
- [x] 1.2 Add `recommend --rerank` (builds `HostedRanker` when a key is set); verify parsing and that the flag is off by default.
- [x] 1.3 Run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
