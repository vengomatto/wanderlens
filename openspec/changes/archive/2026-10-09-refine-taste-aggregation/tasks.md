# Tasks

## 1. Storage

- [x] 1.1 Add a `trip_subjects` table (user_id, trip_id, subject) in `db.py`, with a migration for existing DBs. Verify: a test asserts the table exists and is user-scoped.

## 2. Profile aggregation

- [x] 2.1 Store canonical per-trip attributes during tagging and compute `profile_entries` subject weights as cross-trip recurrence. Verify: a test with two trips shows an attribute in both outweighs one in a single trip, independent of photo counts.

## 3. Faceted scoring

- [x] 3.1 Build per-trip taste facets from `trip_photos` + `photo_embeddings` and score `embedding_score` as the max over facets. Verify: a test where a destination matches the second facet (not the first) still scores high.
- [x] 3.2 Wire facets into `run_recommend` and `run_eval`. Verify: a two-taste profile yields recommendations drawn from both facets.

## 4. Integration & docs

- [x] 4.1 Rebuild the profile from the archive (Malta + Trentino + Misc) and run `recommend`; verify both coastal and alpine destinations appear. Update docs.
