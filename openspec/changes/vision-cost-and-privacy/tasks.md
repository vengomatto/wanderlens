# Tasks

## 1. Prepared vision payload

- [x] 1.1 Add `prepare_image` (EXIF strip, orientation, 512 px cap, JPEG q80) and send `detail: low`; verify a test that the prepared bytes are ≤512 px and carry no EXIF.
- [x] 1.2 Verify the encoded payload is smaller than the original for a large photo.

## 2. Tag cache and new-trip tagging

- [x] 2.1 Add the `tag_cache` table and cache the trip-sample result by input + model + prompt; verify a test that a re-run makes no vision call and `retag` overrides it.
- [x] 2.2 Tag every trip lacking subjects (not only an empty profile); verify a test that a newly added trip is tagged on the next run.

## 3. Estimate

- [x] 3.1 Add `ingest --tag --estimate` that prints the sampled image count and an estimated cost and sends nothing; verify a test/CLI parse.

## 4. Documentation and verification

- [x] 4.1 Update `README.md` for the privacy/cost behaviour and `--estimate`; verify the documented command runs.
- [x] 4.2 Run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
