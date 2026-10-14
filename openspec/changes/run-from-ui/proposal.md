# Proposal

## Why

From `docs/IMPROVEMENT_PLAN.md` (E4): the main loop (change taste, regenerate) needs
a terminal. At single-user scale an in-process background job is enough to let the
dashboard start `ingest`/`recommend` explicitly, without a queue service.

## What Changes

- **User-started jobs.** A tiny in-process runner with a `jobs` table and
  `POST /jobs/{ingest|recommend}` plus `GET /jobs/{id}` status, so the user starts
  work from the UI; a **single-flight** guard prevents overlapping runs.
- **POST safety.** A per-process random token is required on job POSTs.
- **Read-only, refined.** The dashboard no longer *recomputes on view* (unchanged),
  but work may run when the user **explicitly starts a job**.
- No **BREAKING** changes.

## Capabilities

### Modified Capabilities
- `web-interface`: the read-only requirement is refined to "no recomputation on
  view; explicit user-started jobs only", plus a job runner and status.

## Impact

- `wanderlens/db.py`: a `jobs` table.
- `wanderlens/web/jobs.py`: the runner.
- `wanderlens/web/app.py` + templates: job routes, Run buttons, status.
- `wanderlens/pipeline/`: a `run_ingest_job` helper.
- Tests for the runner, the token, and the status fragment.
