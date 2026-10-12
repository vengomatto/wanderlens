# Tasks

## 1. Dependencies and app skeleton

- [x] 1.1 Add a `web` optional-dependency group (`fastapi`, `uvicorn`, `jinja2`) to `pyproject.toml`; verify `pip install -e '.[web]'` succeeds and the existing suite still passes.
- [x] 1.2 Create the `wanderlens/web/` package with an app factory `create_app(config)` in `web/app.py`; verify `python -c "from wanderlens.web.app import create_app"` imports without pulling the model runtime.
- [x] 1.3 Vendor pinned HTMX, Alpine.js and Leaflet assets under `wanderlens/web/static/` with recorded versions; verify the app serves them and works offline.

## 2. Persistence extension

- [x] 2.1 Add `destination_name`, `destination_country`, `destination_lat`, `destination_lon`, `destination_description`, `embedding_score`, `attribute_score` to `recommendations` via an idempotent `db._migrate` step; verify a `tests/test_db.py` case migrates a pre-change database.
- [x] 2.2 Write those fields in `run_recommend` when persisting a run; verify `tests/test_recommend.py` asserts a stored row carries the destination name and both score components.

## 3. View-model seam

- [x] 3.1 Implement `wanderlens/web/views.py` (`profile_view`, `trips_view`, `trip_detail`, `recommendations_view`, `map_points`) so routes contain no SQL; verify unit tests in `tests/test_web_views.py` against a seeded SQLite DB.
- [x] 3.2 Handle absent and partial data (no profile, no recommendations, pre-change rows with NULL columns); verify empty/partial-state unit tests.

## 4. Routes and templates

- [x] 4.1 Add HTML routes `/`, `/recommendations`, `/trips/{id}`, `/map` rendering Jinja templates; verify `TestClient` returns 200 with the expected content in `tests/test_web.py`.
- [x] 4.2 Render guiding empty states instead of errors when profile or recommendations are missing; verify `TestClient` output names the CLI command to run.
- [x] 4.3 Add a test that importing and rendering the web app loads no embedding/vision model; verify it fails if a heavy import is added to `wanderlens/web/`.

## 5. Map and thumbnails

- [x] 5.1 Add a `/photos/{photo_id}` thumbnail route that resolves the path from the current user's `photos` rows and downscales with Pillow; verify it returns an image and 404s for unknown or cross-user ids.
- [x] 5.2 Render the Leaflet map with visited-trip and recommendation markers (OSM tiles, no fame styling yet, per design); verify the page embeds both marker sets and loads the vendored Leaflet.

## 6. CLI and documentation

- [x] 6.1 Add a `serve` subcommand (`--host` default `127.0.0.1`, `--port` default `8000`) that runs the app with uvicorn; verify `tests/test_cli.py` parses it.
- [x] 6.2 Update `README.md` (install `[web]`, `wanderlens serve`) and the `AGENTS.md` commands list; verify the documented serve command starts the app.

## 7. Integration

- [x] 7.1 Walk the full read-only flow through `TestClient` (profile → recommendations → trip detail → map → thumbnail) on a seeded DB; verify every page is 200 and each `web-interface` scenario is exercised.
- [x] 7.2 Run the whole suite with `.venv/bin/python -m pytest -q`; verify it is green.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
