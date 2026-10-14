# Proposal

## Why

From `docs/IMPROVEMENT_PLAN.md` (C2): tagging currently sends a sample to a hosted
vision model — cost, network, and only three photos per trip, so the attribute
signal is thin. The local CLIP model is already computed for every photo and can
score it against short prompts for free.

## What Changes

- **Zero-shot CLIP tagger.** A local tagger scores each photo's CLIP embedding
  against vocabulary prompts and assigns the matching attributes — zero marginal
  cost, private, and covering *every* photo (not a sample).
- **Default tagging path.** `ingest --tag` uses the local tagger by default; the
  hosted VLM is kept for the long tail behind `--vlm`.
- No **BREAKING** changes; the tagger implements the same `describe` seam, so the
  profile pipeline is unchanged and the sample cache still applies.

## Capabilities

### Modified Capabilities
- `taste-profiling`: attribute tagging can run locally with zero-shot CLIP,
  covering every photo, with the hosted model optional.

## Impact

- New `wanderlens/models/tagging.py` (`ZeroShotTagger`).
- `wanderlens/cli/main.py`: `--tag` uses the tagger; `--vlm` opts into hosted.
- `wanderlens/config.py`: a tag-provider setting.
- Tests with a fake embedder for the tagger and the CLI default.
