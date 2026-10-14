# Design

## Context

See `proposal.md`. `rank_destinations` scores candidates by the best taste-facet
match against a text embedding (`destination_text`). Facets and destination text
live in different CLIP modalities. `WikimediaMediaProvider` already gathers a
Destination's curated images; the local embedder can embed images.

## Decisions

### A destination visual vector
`catalog/image_embeddings.py:ensure_destination_image_embeddings` takes the
candidates, the image embedder, and an injectable `fetch_urls(destination,
session)` (default backed by `WikimediaMediaProvider`). For each uncached
Destination it fetches up to `limit` (4) hero images, downloads them (best-effort),
embeds each with `embed_image` (downscaled), and stores their normalized mean in a
catalog-scoped `destination_image_embeddings(destination_id, model, dim, vector,
count, fetched_at)`. Failures skip that Destination, so the run continues.

### Ranking prefers the image vector
`rank_destinations(..., image_vectors=None)`: in the facet branch, if the
Destination has an image vector, the embedding score is the best facet `dot`
against the image vector; otherwise against the text vector. This keeps the text
path as the fallback and the change deterministic.

### Opt-in, gated
`run_recommend(..., image_matching=False, image_fetcher=None, session=None)`
computes image vectors only when enabled (or a fetcher is injected). Off by
default so tests stay hermetic, and the plan gates promotion on `eval --loto`.

## Risks / Trade-offs

- **Cross-modal collapse is unproven to help** → off by default; A0 decides.
- **Network + CPU cost** → cached globally, bounded to 4 images/Destination, and
  only on enabled runs; downloads respect the existing session/backoff.
- **Sparse image coverage** → the text fallback covers Destinations without images.
