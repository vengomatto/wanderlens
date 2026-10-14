# Proposal

## Why

From `docs/IMPROVEMENT_PLAN.md` (C1, C2): `--tag` uploads full-size originals
(with EXIF/GPS) to a hosted model, bills by image size, never caches a result, and
only tags trips when the whole profile is empty — so new trips are silently
untagged unless you re-send every photo.

## What Changes

- **Downscale and strip.** Send a 512 px, EXIF-stripped JPEG at low detail, so
  cost drops roughly an order of magnitude and no GPS/time leaves the machine.
- **Cache per trip sample.** Cache the tag result by input + model + prompt, so a
  re-run does not re-send known photos.
- **Tag new trips automatically.** Tag every trip that lacks subjects, not only
  when the whole profile is empty.
- **Estimate before spending.** `ingest --tag --estimate` prints the number of
  images and an estimated cost, then stops.
- No **BREAKING** changes.

## Capabilities

### Modified Capabilities
- `taste-profiling`: attribute tagging sends downscaled, EXIF-stripped images,
  caches results, and tags new trips automatically.
- `photo-ingestion`: the vision step supports a dry-run estimate.

## Impact

- `wanderlens/models/vision.py`: prepare (resize, strip EXIF, low detail).
- `wanderlens/db.py`: a tag cache table.
- `wanderlens/pipeline/profile.py`: per-sample cache, tag trips lacking subjects.
- `wanderlens/cli/main.py`: `--estimate`.
- Tests for the prepared payload, the cache, new-trip tagging, and the estimate.
