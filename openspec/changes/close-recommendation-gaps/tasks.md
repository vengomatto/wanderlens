# Tasks

## 1. Catalog hygiene

- [ ] 1.1 Add name cleaning (strip parenthetical qualifier, normalize case) and apply it in `catalog/destinations.py` when records become Destinations and when a catalog is loaded; verify a test with a qualifier name and a case test.
- [ ] 1.2 Deduplicate a catalog by normalized (name, country) and bound granularity to `{city, region, area}`; verify a test that a duplicate is removed and granularity is bounded.
- [ ] 1.3 Widen `DEFAULT_CANDIDATE_COUNTRIES`; verify the default build spans more countries than before (test the constant/pool).

## 2. Media refresh and dedupe

- [ ] 2.1 Add `refresh` to `catalog/media.py:fetch_media`/`fetch_media_for`; verify a test that refresh rebuilds cached media and the default keeps the cache.
- [ ] 2.2 Add perceptual (average-hash) near-duplicate detection during download; verify a test that two near-identical images yield one stored file.
- [ ] 2.3 Wire `recommend --refresh-media` / `WANDERLENS_REFRESH_MEDIA`; verify CLI parsing and the flag reaches the fetcher.

## 3. Feedback loop

- [ ] 3.1 Add the user-scoped `feedback` table and read/write helpers (record, latest-wins, list, clear); verify tests.
- [ ] 3.2 Consume feedback in `rank_destinations` as a deterministic bias; verify liked-outranks-equal, disliked-pushed-down, and no-feedback-unchanged tests.
- [ ] 3.3 Wire feedback into `run_recommend` and add the `feedback` CLI command (record/list/clear); verify an end-to-end test and CLI parsing.
- [ ] 3.4 Add feedback buttons and a POST route on the destination page; verify a `TestClient` round-trip records and reflects the action.

## 4. Case on the shortlist and card

- [ ] 4.1 Build cases for the shortlist before final ranking; verify a test that shortlisted destinations have cases.
- [ ] 4.2 Add a case snippet to `RecView` and render it on the recommendation card; verify a `TestClient` render shows it and omits it when absent.

## 5. Grounded itinerary and diaries

- [ ] 5.1 Thread an optional searcher into `gather_guide` and the itinerary synthesizer so days are grounded in search results; verify a test with an injected searcher and a fallback test.
- [ ] 5.2 Add non-empty default travel-blog/diary sources; verify a guide built with no custom blogs still lists diaries.

## 6. Synthetic archive taste

- [ ] 6.1 Write `subjects.json` in `synthetic.materialize` and seed the profile subjects in the `synthetic` command; verify a test that synthetic recommendations reflect attribute matches.

## 7. Documentation and verification

- [ ] 7.1 Update `README.md`/`AGENTS.md` for feedback, media refresh, catalog hygiene, grounded itineraries, and synthetic tags; verify the documented commands run.
- [ ] 7.2 Run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
