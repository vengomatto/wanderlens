# Proposal

## Why

Search-grounded LLM descriptions cost ~$0.007/request — far more than the token
work — to guard against obscure places. OpenStreetMap is a free, keyless source of
**structured features** (coastline, beach, harbour, historic) that map directly to
our shared attribute vocabulary, likely a stronger matching signal than LLM prose.

## What Changes

- Add an **OpenStreetMap provider** (via the free Nominatim search API with
  `extratags`) that derives canonical feature words for a place.
- Insert it into the default provider chain: `wikimedia → openstreetmap → llm`.
- Keep the paid LLM as the last-resort fallback only.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `destination-catalog`: a free OpenStreetMap provider derives destination
  attributes from OSM tags.

## Impact

- `wanderlens/catalog/providers.py` — new `OsmProvider`.
- `wanderlens/config.py` — default provider order includes `openstreetmap`.
- Docs (`README.md`, `docs/ROADMAP.md`).
