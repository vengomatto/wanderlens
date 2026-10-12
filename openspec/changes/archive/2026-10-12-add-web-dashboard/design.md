# Design

## Context

See `proposal.md` for motivation and `specs/web-interface/spec.md` for the
behavior contract.

Current state that shapes the approach:

- `wanderlens/core/` is pure (taste + ranking, ports) and `wanderlens/models/`
  is the only place that imports `onnxruntime`/`tokenizers`; a test
  (`tests/test_embeddings.py`) enforces this by static import scan.
- Persistent state lives in one SQLite file (`wanderlens/db.py`), every row
  user-scoped. `pipeline/profile.py` already has pure read loaders
  (`load_photos`, `show_profile`) and `pipeline/recommend.py` has read loaders
  (`load_profile`, `load_taste_facets`, `load_trip_centers`).
- `run_recommend` returns in-memory `Recommendation` objects but persists only
  `destination_id`, `score`, `rank`, `explanation` — not the destination's
  display fields nor the embedding/attribute components the dashboard needs.
- `Pillow` is already a core dependency; trips store a centroid (`lat`/`lon`).

## Goals / Non-Goals

**Goals:**

- A fast, offline-capable, single-process dashboard with no build step, reusing
  the existing core/pipeline read paths.
- A clean seam so the web layer stays a thin driver and is testable without
  HTTP: a view-model module over the database.
- Keep the model runtime out of the request path entirely.

**Non-Goals:**

- Any mutation or long-running job from the UI (ingest, tag, recommend). Deferred
  to a later change that introduces a worker/queue.
- Authentication, hosting, multi-user isolation beyond the existing `user_id`.
- Live re-ranking or on-demand embedding of destinations.
- A JSON API for a future mobile client (not needed yet; can be added beside the
  HTML routes later).

## Decisions

### Web layer is a driver package, not core

Add `wanderlens/web/` alongside `wanderlens/cli/`. It may import
`fastapi`/`uvicorn`/`jinja2` and read from `db.py` and `pipeline.*`, but
`core/` gains nothing and stays free of external runtimes. The existing static
confinement test already forbids heavy imports anywhere outside `models/`.

*Alternative considered:* putting routes in `cli/`. Rejected — `cli/` is an
argparse entry point; the web app is a separate delivery mechanism with its own
dependencies and tests.

### Stack: FastAPI + Jinja + HTMX + Alpine.js, vendored assets

Server-rendered HTML with Jinja; HTMX for partial navigation/refresh; Alpine.js
for small local interactions (tab/filter/lightbox). Leaflet + OpenStreetMap
tiles (keyless) for the map. HTMX, Alpine.js and Leaflet are **vendored** under
`wanderlens/web/static/` rather than loaded from a CDN, so the app works offline
and stays portable for open-source users. Tiles are the one expected network
fetch and carry no user data.

*Alternatives:* (a) FastAPI JSON + SPA — rejected for the v1 goal: Node build
step, two codebases, slower to iterate while the idea is malleable.
(b) Flask — viable and lighter, but FastAPI + `TestClient` gives typed,
dependency-injectable app factories and a path to a JSON API later.

### A view-model seam over SQLite

Create `wanderlens/web/views.py`: a deep module exposing plain dataclass/dict
view models and nothing HTTP-specific — e.g. `profile_view(conn, user_id)`,
`trips_view(...)`, `trip_detail(...)`, `recommendations_view(...)`,
`map_points(...)`. Route handlers only wire request → view model → template. This
keeps SQL out of routes and templates and lets the dashboard be tested by
calling the seam directly, mirroring how `pipeline` is tested today. Reuse
`pipeline.profile` loaders where they fit; add focused queries for trip photos
and the recommendation join.

### Persist the Recommendation's display fields and score components

Extend the `recommendations` table with `destination_name`,
`destination_country`, `destination_lat`, `destination_lon`,
`destination_description`, `embedding_score`, `attribute_score`; `run_recommend`
writes them when it persists a run. Schema change is additive, applied in
`db._migrate` (same pattern as the `trips.lat/lon` migration), so existing
databases keep working and old rows simply render with fields absent.

*Alternative considered:* have the dashboard reload the catalog and re-derive
destination details, and drop the score components from the view. Rejected — it
either recomputes ranking (a spec non-goal) or loses the "inspectable ranking"
value the recommendation spec already exposes.

### Thumbnails served locally

A route resolves a `photo_id` to its stored path and returns a downscaled
thumbnail generated with Pillow (cached under `data/`), never the original and
never off-host. This keeps pages light without a separate thumbnail pipeline.

### Launch via `wanderlens serve`

Add a `serve` subcommand (`--host` default `127.0.0.1`, `--port` default `8000`)
that builds the app from the same `Config` and runs `uvicorn`. Localhost-only by
default reinforces the single-user, no-auth stance.

## Risks / Trade-offs

- **A user opens the dashboard before running `ingest`/`recommend`** → guiding
  empty states (spec) plus a banner telling them the exact CLI command.
- **Stale recommendations** once photos change → the dashboard shows the
  persisted run and its timestamp; regeneration stays a CLI action in v1.
- **Vendored front-end assets drift from upstream** → small, pinned files with
  recorded versions; upgrade deliberately, not automatically.
- **Additive schema migration on an existing DB** → guarded `ALTER TABLE` in
  `_migrate`, idempotent, with a `test_db` migration test.
- **Serving photos from disk** → resolve only paths present in the `photos`
  table for the current user (no arbitrary path traversal).
- **Heavy model import sneaking into web** → the existing static confinement
  test still covers `wanderlens/web/`; add a dashboard render test that asserts
  no model download/load occurs.

## Migration Plan

1. Additive `ALTER TABLE recommendations` columns via `db._migrate`; no data
   backfill needed (old rows render partial).
2. Ship the CLI `serve` subcommand and the `web` optional dependency group.
3. Rollback: dropping the web package/command leaves the CLI and schema
   untouched; extra columns are harmless if unused.

## Open Questions

- Exact default `port` (8000 vs 8765) — cosmetic, settle at implementation.
- Whether the map's "uncommon vs famous" styling is needed now or waits for the
  popularity signal in the roadmap — deferrable, does not change the approach.
