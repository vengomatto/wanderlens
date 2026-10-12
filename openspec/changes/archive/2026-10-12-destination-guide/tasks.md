# Tasks

## 1. Persistence

- [x] 1.1 Add catalog-scoped `destination_guide` (JSON columns) and `destination_itineraries` tables via the schema/`db._migrate`; verify a `tests/test_db.py` case asserts their columns and that both are non-user-scoped.
- [x] 1.2 Verify a fresh and a legacy database both expose the new tables after `init_db`; verify a migration test.

## 2. Wikivoyage sources

- [x] 2.1 Add a Wikivoyage fetch helper (page lookup via `pageprops`, plaintext extract, wikitext) to `catalog/fetch.py`; verify unit tests with a fake session cover hit and miss.
- [x] 2.2 Parse *see/do* listing templates into points of interest with coordinates; verify tests against a wikitext fixture, including a malformed listing.
- [x] 2.3 Extract external/organisation resource links; verify tests deduplicate and label them.

## 3. Books

- [x] 3.1 Add Wikidata `P840` (narrative location) lookup and an Open Library place/subject search; verify tests with fake responses merge and deduplicate.
- [x] 3.2 Verify a Destination with no books yields an empty reading list without error.

## 4. Climate and films

- [x] 4.1 Add an Open-Meteo monthly climate summary for a coordinate; verify a test with a fake response produces per-month temperature and precipitation.
- [x] 4.2 Add a Wikidata `P840` films/series lookup; verify a test lists works and an empty case omits them.

## 5. Gallery

- [x] 5.1 Raise the Commons gallery limit (and merge article media) so a destination reaches at least ten images where available; verify a test with enough fake images stores ten.

## 6. Guide command

- [x] 6.1 Add a `catalog/guide.py` orchestrator gathering all sections best-effort and writing the cache; verify tests (injected fakes) store partial and full guides.
- [x] 6.2 Add the `wanderlens guide [--count] [--refresh] [--no-llm]` subcommand and make it idempotent (no refetch when cached, `--refresh` forces); verify `tests/test_cli.py` plus a cache test.

## 7. Optional LLM itinerary

- [x] 7.1 Add the `ItinerarySynthesizer` port and a default implementation under `models/` with a pinned model and prompt; verify the model runtime stays confined to `models/`.
- [x] 7.2 Cache synthesised itineraries by evidence fingerprint and reuse them; verify a test asserts a second run does not call the model.
- [x] 7.3 Make synthesis opt-in and non-fatal; verify a test with `--no-llm` and a raising synthesizer still stores the guide.

## 8. Web sections

- [x] 8.1 Add the guide fields to the destination view model; verify `tests/test_web_views.py` covers present and absent sections.
- [x] 8.2 Render the gallery, reading list, resource links, films, and itineraries (AI-labelled) on the destination page; verify `TestClient` renders each and omits empties.
- [x] 8.3 Plot points of interest on the regional map and add the monthly climate view; verify `TestClient` embeds the POI GeoJSON and the climate data.
- [x] 8.4 Add similar destinations from cached embeddings; verify both the similar and empty branches.

## 9. Documentation and integration

- [x] 9.1 Update `README.md`/`AGENTS.md` for `wanderlens guide` and its flags; verify the documented command runs.
- [x] 9.2 Walk `guide` → destination page with cached guide and no network; verify every page is 200 and `.venv/bin/python -m pytest -q` is green.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
