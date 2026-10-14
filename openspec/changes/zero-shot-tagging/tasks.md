# Tasks

## 1. Local tagger

- [x] 1.1 Add `models/tagging.py` with `ZeroShotTagger` (prompt embeddings, softmax scoring, top-k labels) implementing the `describe` seam; verify a test with a fake embedder that a photo near a prompt's vector gains that attribute.
- [x] 1.2 Verify canonical labels map through `canonicalize` and that the tagger reports a distinct `model`/`prompt_version` so its cache is separate.

## 2. Default path and opt-in

- [x] 2.1 Make `ingest --tag` use the local tagger by default and add `--vlm` for the hosted model; verify CLI parsing and a test that the default constructs the local tagger.
- [x] 2.2 Add `config.tag_provider` (`clip` default); verify the config parses it.

## 3. Documentation and verification

- [x] 3.1 Update `README.md` for local-by-default tagging and `--vlm`; verify the documented command runs.
- [x] 3.2 Run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
