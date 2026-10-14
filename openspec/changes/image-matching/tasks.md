# Tasks

## 1. Image-to-image scoring

- [x] 1.1 Add an `image_vectors` term to `rank_destinations` (best facet match against the image vector, text fallback); verify tests for image-preferred, text-fallback, and off-by-default.
- [x] 1.2 Add the `destination_image_embeddings` table and a cache-aware builder that fetches, embeds, and stores a Destination's visual vector; verify tests with an injected URL fetcher and fake embedder (derives, caches, tolerates failure).

## 2. Wiring

- [x] 2.1 Add `image_matching` to `run_recommend` (off by default, injectable fetcher) and compute image vectors for candidates when enabled; verify a test that ranking uses them and that failures fall back.
- [x] 2.2 Add `config.image_matching` and `recommend --image-matching`; verify config parse and CLI parse.

## 3. Documentation and verification

- [x] 3.1 Update `README.md` for image matching; verify the documented command runs.
- [x] 3.2 Run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
