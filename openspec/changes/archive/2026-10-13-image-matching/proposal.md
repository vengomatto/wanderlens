# Proposal

## Why

From `docs/IMPROVEMENT_PLAN.md` (A2, L4): taste is built from photos, but
candidates are matched photo-vector to *text*-vector, a cross-modal comparison
whose similarities are compressed (unrelated places score 0.84–0.92). Comparing a
photo vector to a destination's *image* vector is a direct comparison and spreads
out much more. This is the plan's biggest quality lever.

## What Changes

- **Destination image embeddings.** Fetch 3–5 hero images per candidate
  (Wikidata P18, the article's media, the Commons category), downscale, embed
  with CLIP vision, and store a per-destination vector — cached globally, once.
- **Image-first scoring.** Score a candidate by the best taste-facet match against
  its image vector, with the text vector as the fallback when no image exists.
- **Opt-in and gated.** Off by default; enabled per run and judged against the
  `eval --loto` metrics before it becomes a default.
- No **BREAKING** changes.

## Capabilities

### New Capabilities
- `image-matching`: destination image embeddings and image-to-image scoring.

### Modified Capabilities
- `recommendation`: the embedding term prefers the image vector when available.

## Impact

- `wanderlens/core/recommend.py`: an `image_vectors` term in ranking.
- `wanderlens/catalog/image_embeddings.py`: fetch hero images + embed + cache.
- `wanderlens/db.py`: `destination_image_embeddings` (catalog-scoped).
- `wanderlens/pipeline/recommend.py`: wire it, injectable, off by default.
- `wanderlens/cli/main.py`, `config.py`: `--image-matching` / `WANDERLENS_IMAGE_MATCHING`.
- Tests for the scoring term, the cache, and the fallback.
