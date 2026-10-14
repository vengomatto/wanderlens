# Tasks

- [x] 1.1 Add the `jobs` table and `web/jobs.py` single-flight runner (injectable fn); verify tests that a job runs to done, a second is refused while running, and an error is recorded.
- [x] 1.2 Add `POST /jobs/{kind}` (token-required, single-flight, 303) and `GET /jobs/{id}` + `/jobs/latest` status fragments; verify tests for the token rejection, job creation, and status.
- [x] 1.3 Add a Pipeline card on the profile page (Run ingest / Run recommend + polling status) and inject the post token into forms; verify a `TestClient` render.
- [x] 1.4 Refine the read-only spec (done in the delta) and update `README.md`; run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
