# Tasks

## 1. Description fetchers

- [ ] 1.1 Add `fetch_wikipedia_summary(name, country)` and `fetch_wikidata_description(name)` in `catalog/fetch.py` using injectable sessions. Verify: tests with a mocked session assert the parsed description.
- [ ] 1.2 Add `enrich_records(records, fetch)` that sets each record's `description` when empty, leaving it empty on failure. Verify: a test enriches records with a stub fetcher and tolerates a raising one.

## 2. Catalog integration

- [ ] 2.1 Wire enrichment into catalog building (`default_catalog` / `_eval_catalog`), using the cache so already-described records are not refetched. Verify: a test builds a catalog with a stub fetcher, saves, reloads, and asserts no second fetch.
- [ ] 2.2 Confirm ranking uses descriptions (`destination_text`) and falls back to `name, country`. Verify: a test shows a described destination ranks above an identical undescribed one for a matching taste.

## 3. Integration & docs

- [ ] 3.1 Rebuild the enriched catalog and re-run `eval` on the Malta archive. Verify: `eval` reports a resurfacing result and the ranking is visibly affected by descriptions.
- [ ] 3.2 Update `docs/ROADMAP.md` to reflect the enrichment and any remaining limitation. Verify: the "destination text is thin" limitation is amended.
