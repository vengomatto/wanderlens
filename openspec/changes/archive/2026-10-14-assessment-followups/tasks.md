# Tasks

- [x] 1.1 Make `check_regression` relative, update `scripts/eval.sh`, refresh `docs/eval-baseline.json` from a real LOTO run; verify a test that a small drop fails.
- [x] 1.2 Add `run_recommend_ui` and use it in the dashboard job so UI and CLI agree; verify a test that the job uses the shared options.
- [x] 1.3 Require the token on feedback and brief POSTs; verify rejection without it and success with it.
- [x] 1.4 Stop Explore overflow at phone width; verify the grid CSS.
- [x] 1.5 Run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
