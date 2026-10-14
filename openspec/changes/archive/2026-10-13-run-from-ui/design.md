# Design

## Context

See `proposal.md`. The dashboard is FastAPI, bound to localhost, with HTMX. The
pipeline functions (`run_ingest`, `run_profile`, `run_recommend`) are synchronous.

## Decisions

### In-process single-flight runner
`web/jobs.py:JobRunner` holds a lock and a single worker thread. `submit(kind,
fn)` refuses if a job is running; otherwise it inserts a `jobs` row
(`queued`), starts a thread that sets `running`, calls `fn`, records
`done`/`error` and a message, and releases the lock. State lives in the DB so a
status request from any worker/process sees it. No Celery/Redis.

### Endpoints and token
`app.state.post_token = secrets.token_urlsafe(24)` at startup; the render context
exposes it to forms. `POST /jobs/{kind}` (query `token`, `kind ∈ ingest|recommend`)
validates the token, creates + submits the job, and returns a 303 to the profile.
`GET /jobs/{id}` renders a status fragment for HTMX polling. `GET /jobs/latest`
renders the newest job's status.

### What the jobs run
`pipeline/recommend.py:run_ingest_job(config, user_name)` does `run_ingest` +
`run_profile`; the recommend job calls `run_recommend` with sane defaults. Both
run on the app's config.

## Risks / Trade-offs

- **Heavy CLIP work in a thread** → acceptable single-user; the UI polls status.
- **Token in a GET-looking form** → it is a POST query param, validated; localhost
  only.
- **A crashed job** → recorded as `error` with the message; the lock is released.
