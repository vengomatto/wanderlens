# Proposal

## Why

Two weaknesses cap suggestion quality. First, the top-k are often **near-
duplicate** — a coastal profile gets eight coastal areas — because each is scored
independently. Second, there is **no fame/novelty signal**, so the app cannot
surface the *uncommon* places that justify using it over a search engine. Both are
cheap to fix on top of the existing ranking.

## What Changes

- **Diversify the ranked list** with Maximal Marginal Relevance (MMR): after
  scoring, select destinations that are both high-scoring and dissimilar from
  those already chosen, so the list is not eight variations of one vibe.
  Deterministic, with a tunable `diversity` weight.
- **Popularity signal**: fetch each Destination's popularity from **Wikimedia
  pageviews** (free, keyless), cache it, and expose it as a **famous ↔ uncommon**
  label.
- **Novelty preference**: a knob (`familiar | balanced | uncommon`) that biases
  selection toward well-known or off-the-beaten-path places.
- Expose popularity and the label on the recommendation card and destination page.
- CLI: `recommend --diversity` and `recommend --novelty`. No **BREAKING** changes.

## Capabilities

### New Capabilities
- `destination-popularity`: fetches and caches a Destination's popularity from a
  free source, so the app can distinguish famous from uncommon places.

### Modified Capabilities
- `recommendation`: the ranked list is diversified (MMR); a novelty preference
  biases selection; popularity is carried on each Recommendation.
- `web-interface`: the recommendation card and destination page show a
  famous/uncommon label.

## Impact

- `wanderlens/core/recommend.py`: MMR selection and the novelty bias.
- `wanderlens/catalog/popularity.py`: Wikimedia pageviews fetch + cache; a
  catalog-scoped `destination_popularity` table.
- `wanderlens/pipeline/recommend.py`: fetch popularity best-effort, persist it,
  pass the diversity/novelty settings.
- `wanderlens/db.py`: additive `destination_popularity` table and recommendation
  columns.
- `wanderlens/cli/`: `--diversity`, `--novelty` flags; `wanderlens/web/`: the
  label.
- New tests for MMR, the novelty bias, popularity caching, and the label.
