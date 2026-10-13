# Tasks

## 1. CLIP text truncation (L1)

- [x] 1.1 Add a pure `_truncate_with_eos` helper and use it in `_encode_text`; verify a test that long inputs keep the end token and differ from each other.
- [x] 1.2 Add a `cache_key` to the embedder and key `destination_embeddings` by it; verify a test that the key changed and a missing entry is recomputed.

## 2. Percentile popularity (A5.1)

- [x] 2.1 Add `percentile_labels` and use it in ranking when popularity is present; verify a test that the labels split roughly in thirds and no bucket is a majority.

## 3. Evaluation harness (A0)

- [x] 3.1 Add MRR and Recall@k helpers to `core/evaluate.py`; verify deterministic unit tests.
- [x] 3.2 Add a leave-one-trip-out runner and a `recommend --diagnose` breakdown (component spread, collapsed-vector share, top-20 mix); verify tests with injected fakes.
- [x] 3.3 Add `scripts/eval.sh` with a baseline gate; verify it prints metrics and exits non-zero on a regression.

## 4. Pipeline quick wins

- [x] 4.1 Strip wikitext headings and cut descriptions at a sentence boundary; verify tests.
- [x] 4.2 Skip and count unreadable photos in `_embed_photos`; verify a test with a failing embedder.
- [x] 4.3 Build cases for the final recommendations only; verify a test that the shortlist is not cased.

## 5. Documentation and verification

- [x] 5.1 Update `README.md`/`docs/IMPROVEMENT_PLAN.md` note for the new eval and diagnostics; verify the commands run.
- [x] 5.2 Run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
