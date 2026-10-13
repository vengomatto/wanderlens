# Tasks

## 1. Runnable synthetic archive

- [x] 1.1 Extend `core/gallery.py` with a data-only description of a broad mock archive (many trips, coordinates, dates, attributes; many matching and non-matching Destinations); verify a test that the description is deterministic.
- [x] 1.2 Add a materialiser that writes EXIF-tagged JPEGs plus a `destinations.json` catalog into a target directory; verify a test that the written files parse back through the normal readers.
- [x] 1.3 Add a CLI path (e.g. `eval --materialize <dir>` or a `synthetic` command) that generates the archive; verify running `ingest` then `recommend` over it produces expected matches, and document the command.

## 2. Quality-tiered, pluggable media

- [x] 2.1 Add a `MediaSourceProvider` port in `core/ports.py` and route `catalog/media.py` through it; verify the existing Wikimedia/Commons behavior is unchanged by the refactor.
- [x] 2.2 Rank Commons *Quality/Featured/Valued* images ahead of generic ones (via `extmetadata` categories), raise the width floor, prefer landscape, and drop near-duplicates; verify tests for tier preference, orientation, and dedupe.
- [x] 2.3 Add optional Openverse/Unsplash/Pexels providers enabled only when their key is set; verify a test with an injected fake provider and a disabled-by-default test.
- [x] 2.4 Add outbound external photo-search links (Commons, Google Images, Getty) and ensure no proprietary image is ever downloaded; verify a test that links are present and only open-licensed files are stored.

## 3. Itineraries, diaries, and structured descriptions

- [x] 3.1 Add a deterministic POI-based itinerary builder in `catalog/guide.py` used when no synthesizer is configured; verify a test that a guide with POIs and no key gets a day-by-day itinerary.
- [x] 3.2 Gather travel diaries/journals from the travel guide's links plus a configurable `travel_blogs` list; add a `diaries` column via an additive migration; verify a test for gathering and dedupe.
- [x] 3.3 Structure the destination description into a lead plus highlights; verify a test that the structure is produced and the raw extract remains the fallback.

## 4. Sourced destination case

- [x] 4.1 Add `catalog/case.py` that assembles a keyless case (narrative + citation links) from free sources; verify a test for the keyless case and partial coverage.
- [x] 4.2 Add `models/case.py` with a hosted writer taking a `SearchProvider` (keyed) and the text model, grounded in gathered facts; wire it behind config; verify a test with injected fakes that the narrative is used and cited.
- [x] 4.3 Add the user-scoped `destination_case` cache table and cache by input+model+prompt; verify a test that a second build reuses the cache and that a model/search error falls back to the keyless case without failing the run.

## 5. Web rendering

- [x] 5.1 Render the case (narrative + citations) on the destination page from cache only; verify a `TestClient` render shows it and omits it when absent.
- [x] 5.2 Render itineraries (including the deterministic one), diaries, the structured description, and external photo-search links; verify renders show each and an external search test that no proprietary image URL is embedded.
- [x] 5.3 Verify map/overview pages still render with the new fields and that the destination page never calls an external service at render time (`test_web`).

## 6. Documentation and verification

- [x] 6.1 Update `README.md`/`AGENTS.md` for the synthetic archive command, the media sources and link-outs, deterministic itineraries, diaries, and the case (and the key/config it uses); verify the documented commands run.
- [x] 6.2 Run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
