# Tasks

## 1. Source helpers

- [x] 1.1 Add batched `imageinfo` resolution (titles → url/size/mime/extmetadata) to `catalog/fetch.py`; verify unit tests with a fake session.
- [x] 1.2 Add Wikidata `P18` (item image) and Wikipedia article-media (`prop=images`) helpers; verify tests cover hit and miss.
- [x] 1.3 Add a Commons-category helper (Wikidata `P373` with name fallback, `categorymembers`); verify tests cover both paths.

## 2. Quality filter

- [x] 2.1 Implement the image quality filter (mime, minimum width, blocklist) with deduplication; verify tests drop icons/logos/maps, low-resolution files, and duplicates while keeping photos.

## 3. Provider rework

- [x] 3.1 Rebuild `WikimediaMediaProvider` to assemble the gallery from the curated chain (item image → article media → Commons category), hero first; verify a test with fake sources yields the expected ordered gallery.
- [x] 3.2 Use the proximity search only as a fallback below the threshold; verify tests for both the engaged and not-engaged branches.

## 4. Integration

- [x] 4.1 Update the media tests so the gallery-of-ten case is satisfied by curated sources; verify `tests/test_media.py` is green.
- [x] 4.2 Verify end-to-end that `fetch_media` still caches curated images and attribution with no schema change; verify `tests/test_guide.py`/`tests/test_web.py` remain green.

## 5. Documentation and verification

- [x] 5.1 Note the curated image sourcing in `README.md`; verify the wording matches behaviour.
- [x] 5.2 Run `.venv/bin/python -m pytest -q`; verify it is green.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
