# Proposal

## Why

The held-out evaluation for Malta did not resurface, because catalogue
Destinations built from GeoNames carry only a `Name, Country` string. CLIP has no
meaningful representation for an arbitrary proper noun, so every candidate scored
almost identically and the ranking — and therefore the evaluation — carried no
signal. See `docs/ROADMAP.md` (Known limitations) and
`openspec/changes/archive/2026-10-09-wanderlens-v1/`.

## What Changes

- Enrich candidate **Destinations** with a short natural-language description
  sourced from Wikimedia (Wikidata short descriptions, falling back to Wikipedia
  first-sentence extracts).
- Cache enriched Destinations locally so descriptions are fetched once.
- Ranking already embeds `destination_text`; with real descriptions it now embeds
  meaningful language instead of bare names.
- Degrade gracefully when no description is found or the network is unavailable.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `destination-catalog`: Destinations now carry a descriptive text (not just a
  name), fetched from Wikimedia and cached locally.

## Impact

- `wanderlens/catalog/fetch.py` — description fetching + enrichment.
- `wanderlens/pipeline/recommend.py` / `evaluate.py` — catalog building enriches
  before caching.
- Network calls to `wikidata.org` / `wikipedia.org` at catalog-build time only,
  cached in `data/catalog/destinations.json`.
