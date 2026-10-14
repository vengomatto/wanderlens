# Design

## Context

See `proposal.md`. `models/vision.py` base64-encodes the original file and never
strips EXIF. `pipeline/profile.py` calls `_store_subjects` only when the subjects
table is empty or `--retag`. There is no tag cache.

## Decisions

### Prepared payload
`models/vision.py` gains `prepare_image(path) -> bytes`: open with Pillow, apply
`ImageOps.exif_transpose`, convert to RGB, `thumbnail((512, 512))`, save JPEG
quality 80 into a buffer. `_encode` base64s those bytes, and `describe` sends
`{"type": "image_url", "image_url": {"url": ..., "detail": "low"}}`. Pure and
testable: assert the prepared bytes decode to ≤512 px with an empty EXIF.

### Trip-sample tag cache
New table `tag_cache(user_id, input_hash, model, prompt_version, tags,
created_at)`, `input_hash` = sha256 of the sorted sampled photo sha256s. In
`_store_subjects`, per trip: compute the sample, the digest, and the model/prompt
key; reuse the cached tags, else call the vision model and store. `--retag`
bypasses the cache. The existing per-trip batching and recurrence counting are
kept.

### Tag trips lacking subjects
`run_profile` calls `_store_subjects` whenever `vision is not None` (cache makes
re-runs free) instead of gating on an empty subjects table. Because the digest is
per sample and cached, existing trips are not re-sent; new trips are.

### Estimate
`ingest --tag --estimate` clusters the loaded photos without embedding, counts the
sampled images, prints the count and an estimated cost from a small constant, and
exits before any network call. The cost constant is documented as approximate.

## Risks / Trade-offs

- **Per-sample cache, not per-photo** → a changed sample re-sends the whole trip's
  sample; acceptable, and simpler than attributing a batch result per photo.
- **Zero-shot CLIP tagging (plan C2) and the vision downscale overlap** → this
  change keeps the hosted path but makes it cheap and private; C2 is a follow-up
  that removes most calls entirely.
- **Estimate is approximate** → labelled as such.
