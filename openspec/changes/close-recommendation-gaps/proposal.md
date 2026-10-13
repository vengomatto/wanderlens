# Proposal

## Why

The recommendation *machinery* is now rich, but four gaps still cap the felt
quality: (a) the catalog is dirty and narrow, so the pool is weak; (b) improved
image quality never reaches already-cached destinations, and near-duplicates
survive; (c) there is no feedback loop, so taste is frozen at ingest; (d) the
case/description only appear on the destination page, not where the choice is
made. Two smaller gaps remain: diaries/search are thin, and the LLM itinerary is
not actually search-grounded.

## What Changes

- **Catalog hygiene.** Normalize destination names (strip parenthetical
  qualifiers, title-case), deduplicate by (name, country), assign coherent
  granularity, and widen the default candidate countries.
- **Media refresh + perceptual dedupe.** A `--refresh-media` path (and config)
  re-fetches media so new quality tiering applies to existing destinations, and
  near-duplicate images are dropped by perceptual hash, not just title.
- **Feedback loop.** Record `save | like | dislike | skip` per Destination
  (user-scoped) and bias ranking by it; expose it on the CLI and the dashboard.
  Deterministic when there is no feedback.
- **Surface the case where the choice is made.** Build cases for the whole
  shortlist and show a case snippet / highlights on the recommendation card, not
  only the destination page.
- **Richer diaries and search.** Non-empty default travel-blog sources plus an
  optional keyed search provider alongside DuckDuckGo.
- **Search-grounded itinerary.** Feed web-search results into the LLM itinerary
  so it is grounded, as the guide spec already claims.
- **Synthetic archive exercises taste.** Tag synthetic trips so attribute
  matching (not just embeddings) is exercised end-to-end.
- No **BREAKING** changes; every new step is optional and cached/cached-fallback.

## Capabilities

### New Capabilities
- `feedback`: records a user's save/like/dislike/skip on a Destination and biases
  subsequent recommendations by it.

### Modified Capabilities
- `destination-catalog`: names normalized, duplicates removed, granularity made
  coherent, candidate countries widened.
- `destination-media`: refresh path for cached destinations; perceptual
  near-duplicate detection.
- `destination-case`: cases built for the shortlist and surfaced on cards.
- `destination-guide`: diary sources and optional keyed search; search-grounded
  itinerary.
- `recommendation`: ranking consumes the feedback signal.
- `synthetic-archive`: generated trips carry tags so attribute taste is exercised.

## Impact

- `wanderlens/catalog/destinations.py` / `fetch.py` / `wikivoyage.py`: catalog
  normalization and wider countries.
- `wanderlens/catalog/media.py`: `refresh` flag, perceptual hash dedupe.
- `wanderlens/core/db.py`, `db.py`: `feedback` table (user-scoped).
- `wanderlens/core/recommend.py`: feedback bias term.
- `wanderlens/pipeline/recommend.py`, `cli/`: feedback wiring, `--refresh-media`.
- `wanderlens/catalog/case.py`, `web/`: shortlist cases + card snippet.
- `wanderlens/models/ranker.py`: search-grounded itinerary.
- `wanderlens/synthetic.py`: tagged trips.
- New tests for catalog hygiene, perceptual dedupe, feedback ranking, shortlist
  cases, search-grounded itinerary, and synthetic tags.
