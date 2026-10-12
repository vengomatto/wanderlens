# Tasks

## 1. Persistence

- [x] 1.1 Add catalog-scoped `destination_media` and `destination_images` tables to the schema in `db.py`; verify a `tests/test_db.py` case asserts their columns.
- [x] 1.2 Verify a fresh database and one created before this change both expose the new tables after `init_db`; verify a migration test.

## 2. Media provider chain

- [x] 2.1 Add a `DestinationMediaProvider` Protocol and a media bundle type to `core/ports.py`/`core/models.py`; verify `wanderlens/web` and other non-model packages still import no heavy runtime.
- [x] 2.2 Add Wikipedia page-image, long-extract, and Commons geosearch helpers to `catalog/fetch.py`; verify unit tests with a fake HTTP session cover hits and misses.
- [x] 2.3 Implement the ordered `catalog/media.py` chain that writes image files under `data/media/` and rows into `destination_media`/`destination_images`; verify tests with a fake session.
- [x] 2.4 Record negative/empty results so a miss is not refetched; verify a test asserts no provider call on the second run.

## 3. Region geometry

- [x] 3.1 Implement the region resolver (Wikidata `P402` → Nominatim `polygon_geojson` → granularity-sized circle) with simplification and a `region_kind` flag; verify tests cover precise, approximate, and no-coordinate cases.
- [x] 3.2 Verify simplified polygons stay within a point cap and remain valid GeoJSON.

## 4. Recommend integration

- [x] 4.1 Fetch and cache media for the returned Recommendations inside `run_recommend`, idempotently, and add a `--no-media` CLI flag; verify a test (injected fake media source) stores media and the flag is parsed.
- [x] 4.2 Ensure a media provider error never fails `run_recommend`; verify a test with a raising provider still returns recommendations.

## 5. View models

- [x] 5.1 Add `destination_detail` to `web/views.py` (recommendation row + media + images + region); verify tests cover present and missing media.
- [x] 5.2 Add `similar_trips` ranking the user's trips by cached embedding similarity (numpy only, no model); verify tests with seeded vectors and the empty case.
- [x] 5.3 Add a local destination-image route resolving the filename from `destination_images`; verify it returns an image and 404s for unknown ids without leaking paths.

## 6. Web UI

- [x] 6.1 Redesign Recommendation cards with a hero image or placeholder, a link to the destination page, and an SVG radial score gauge; verify `TestClient` output in `tests/test_web.py`.
- [x] 6.2 Add the `/destinations/{id}` page: hero image, expanded extract, source link and attribution, "why this is for you", and facts; verify `TestClient` renders it and degrades without media.
- [x] 6.3 Add the dual maps: a world locator plus a regional map drawing the region GeoJSON, labelled approximate when so, on the Carto keyless basemap; verify the page embeds the GeoJSON, Leaflet, and Carto tiles.
- [x] 6.4 Add the similar-visits photo strip, omitted when no trip is similar; verify both branches.
- [x] 6.5 Add View Transitions, skeleton loaders, and hover/motion styling; verify assets are served and the pages reference them.

## 7. Documentation and integration

- [x] 7.1 Update `README.md` and `AGENTS.md` for media fetching (`--no-media`) and the destination pages; verify the documented commands run.
- [x] 7.2 Walk the full flow through `TestClient` (recommendations → destination page → maps → image → similar visits) with cached media and no network; verify every page is 200 and `.venv/bin/python -m pytest -q` is green.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
