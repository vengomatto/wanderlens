# Tasks

- [x] 1.1 Add the `traveller_brief` table and `pipeline/brief.py` (save/load, partial upsert); verify tests for saving, loading, and the empty case.
- [x] 1.2 Apply the brief in `run_recommend`: filter candidates by distance from home and use the brief's season; verify tests for exclusion and the season hand-off.
- [x] 1.3 Add the `brief` CLI command (view/set); verify parsing and a save round-trip.
- [x] 1.4 Show and edit the brief on the taste page; verify a `TestClient` render and a save POST.
- [x] 1.5 Update `README.md`; run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
