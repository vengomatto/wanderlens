# Tasks

## 1. Provider

- [x] 1.1 Add `OsmProvider` in `catalog/providers.py` (Nominatim search + `extratags` → canonical feature words), keyless, with a test using a mocked session. Verify: a mocked OSM response yields feature text; an empty response returns `None`.

## 2. Wiring & integration

- [x] 2.1 Add `openstreetmap` to `build_provider_chain` and the default order in config, after `wikimedia` and before `llm`. Verify: a test builds the default chain as `[wikimedia, openstreetmap, llm]`.
- [x] 2.2 Integration: enrich a couple of real places through the OSM provider and confirm feature words and no fee. Verify: a real call returns attributes for a coastal town.

## 3. Docs

- [x] 3.1 Update `README.md` / `docs/ROADMAP.md` with the free OSM provider and the new default chain. Verify: docs list the chain order and note it is keyless/free.
