# Tasks

## 1. Scaffold & environment

- [x] 1.1 Create the Python package layout (`core/`, `sources/`, `catalog/`, `models/`, `pipeline/`, `cli/`), `pyproject.toml`, and a pytest setup. Verify: `pytest` runs green and `python -m wanderlens --help` prints usage.
- [x] 1.2 Add configuration and secret loading (photo-folder path, data dir, model/API keys from env). Verify: a test loads a sample config and resolves a key from the environment.
- [x] 1.3 Create the SQLite schema and initializer with user-scoped tables (users, photos, trips, profile entries, recommendations). Verify: a migration test asserts all tables exist and every table carries `user_id`.

## 2. Photo ingestion

- [x] 2.1 Define the Photo Source port and the Photo model in `core/`. Verify: a unit test ingests from a fake in-memory source.
- [x] 2.2 Implement the local-folder adapter with supported-image discovery. Verify: a test over a temp folder with two images and one `.txt` enumerates exactly the images.
- [x] 2.3 Extract EXIF capture time, GPS, and dimensions, tolerating missing fields. Verify: tests for a photo with GPS and one without.
- [x] 2.4 Make ingestion idempotent, keyed by source plus content hash. Verify: re-ingesting the same folder adds no rows.
- [x] 2.5 Integration: ingest `data/photos` (89 JPEGs + 1 MP4). Verify: the DB holds 89 photos, the video is skipped, and at least one photo has GPS.

## 3. Taste profiling

- [x] 3.1 Cluster photos into trips by capture-time gap and GPS proximity. Verify: a test splits a synthetic set into the expected one vs. two trips.
- [x] 3.2 Reverse-geocode trips offline from GeoNames. Verify: a test resolves Malta coordinates to the expected country and city.
- [x] 3.3 Wrap a local CLIP embedder behind `models/`. Verify: a test produces a vector of the expected dimension; composition stays inside `models/`.
- [x] 3.4 Tag a representative sample per trip via the hosted VLM behind the model seam. Verify: with a stubbed VLM response a trip gains tags; real calls are opt-in.
- [x] 3.5 Persist the Taste Profile (visited geography, aggregated embeddings, tags) user-scoped. Verify: reading the profile returns the stored Preference Factors.
- [x] 3.6 Integration: build the profile from the ingested archive. Verify: `profile show` prints geography, aesthetics, and subjects for the user.

## 4. Destination catalog

- [x] 4.1 Define the catalog port, the Destination model, and one shared attribute vocabulary. Verify: a model test round-trips a Destination.
- [x] 4.2 Fetch Wikidata/GeoNames records, normalize them, and cache locally. Verify: fixture records from two sources normalize to one Destination shape.
- [x] 4.3 Resolve geo names offline. Verify: name resolution succeeds with network access disabled.

## 5. Recommendation

- [x] 5.1 Exclude already-visited places from candidates. Verify: a test shows a visited place is never returned.
- [x] 5.2 Shortlist candidates by embedding similarity to the Taste Profile. Verify: a fixture produces a deterministic shortlist.
- [x] 5.3 Re-rank with the LLM and generate photo-grounded explanations. Verify: a stubbed model yields an explanation and two runs with identical inputs rank identically.
- [x] 5.4 Bound output by the requested count. Verify: `--count N` returns at most N, ranked.
- [x] 5.5 Integration: run `recommend --count 5` against the real profile. Verify: five explained Recommendations, none already visited.

## 6. Evaluation

- [x] 6.1 Implement hold-out of a visited place from the profile. Verify: a test confirms the held-out place is removed from the profile used for the check.
- [x] 6.2 Report outcome and rank of the held-out place. Verify: `eval` prints whether the place was recommended and at what rank.
- [x] 6.3 Integration: run `eval` against the Malta archive. Verify: it reports a resurfacing result for the held-out place.

## 7. CLI & docs

- [x] 7.1 Wire `ingest`, `profile show`, `recommend`, and `eval` commands. Verify: each `--help` works and a smoke run of each against a fixture exits 0.
- [x] 7.2 End-to-end smoke run over `data/photos`. Verify: the script exits 0 and prints the expected sections.
- [x] 7.3 Write the README quickstart and record the test command in `AGENTS.md`. Verify: documented commands match the real CLI.

## Workflow follow-up

- After review, archive this change with `/opsx-archive` so the specs move into `openspec/specs/`.
- Then start implementation with `/opsx-apply`.
