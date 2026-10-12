# Proposal

## Why

Wanderlens v1 is finished but its value is only visible through a terminal: the
Taste Profile and the ranked Recommendations (with their explanation and score
components) are tedious to read and impossible to explore spatially. A
lightweight local web dashboard makes the core loop — *your photos → your taste →
new places* — visible and pleasant, while the app is still malleable and before
a native mobile client (a much larger, less agile bet) is justified.

## What Changes

- Add a **web dashboard** served on localhost, layered on the same `core/` and
  read paths as the CLI. Stack: **FastAPI + Jinja + HTMX**, with **Alpine.js**
  for small client-side interactions. No build step, no Node toolchain.
- Three read-only views:
  - **Taste Profile** — trips, visited geography weights, subject/activity
    weights, aesthetic coverage.
  - **Recommendations** — ranked cards with destination, score and its
    embedding/attribute components, the explanation, and a map.
  - **Trip detail** — the user's own Photos for a trip (thumbnails) plus the
    trip's attributes and location, as evidence behind the taste.
- A map (Leaflet + OpenStreetMap tiles, keyless) plotting visited trips and
  recommended Destinations.
- A `wanderlens serve` CLI subcommand to launch the dashboard locally.
- **Read-only in v1**: the dashboard displays persisted data and never triggers
  ingestion, tagging, or recommendation runs. Launching long CPU jobs from the UI
  is explicitly deferred (it needs a worker/queue, see `docs/ROADMAP.md`).
- No **BREAKING** changes: `core/` behavior, the CLI, and persisted data are
  untouched.

## Capabilities

### New Capabilities
- `web-interface`: a local, read-only web presentation of the Taste Profile,
  visited Trips, and Recommendations, reusing the existing core read paths.

### Modified Capabilities
<!-- None. The dashboard is a new presentation layer; existing requirement-level behavior is unchanged. -->

## Impact

- New package `wanderlens/web/` (app, routes, view models, templates, static
  assets) — a driver/adapter, like `cli/`, not `core/`.
- New `serve` subcommand in `wanderlens/cli/main.py`.
- New optional dependency group `web` in `pyproject.toml` (`fastapi`, `uvicorn`,
  `jinja2`). Small front-end libs (HTMX, Alpine.js, Leaflet) vendored as static
  files so the app works offline and needs no build.
- Small additive persistence change so the dashboard renders purely from the
  database: `run_recommend` also stores each Recommendation's destination name,
  country, coordinates, description, and its embedding/attribute score
  components (an additive migration in `db.py`; no requirement-level behavior
  change).
- The web layer reads only the database and the existing `pipeline.profile`
  loaders; it imports no model runtime.
- New tests: page rendering against a seeded SQLite DB, and a confinement test
  that the web package imports no model runtime.
