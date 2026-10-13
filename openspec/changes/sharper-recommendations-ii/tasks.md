# Tasks

## 1. Correct, information-aware attribute matching

- [ ] 1.1 Replace substring matching in `core/vocabulary.py:canonicalize` with word-boundary/token matching (multi-word synonyms matched as token sequences); verify a test that `"earth"` no longer yields `museum` and existing tag→attribute cases still pass.
- [ ] 1.2 Add an IDF specificity term computed deterministically over the candidate catalog; verify a test where a rare matching attribute outranks a generic one for otherwise equal candidates.
- [ ] 1.3 Expand the vocabulary to cover common thin-matching terms (bay/abbaye/walkway-class errors); verify tests for the new terms and for absence of the old false positives.

## 2. Robust facets and configurable splitting

- [ ] 2.1 Make `core/taste.py:cluster_into_trips` take `max_gap` / `max_jump_km` from injected parameters/config with today's values as defaults; verify a test that default splitting is unchanged and a test that a configured window splits differently.
- [ ] 2.2 Record each trip's photo count and weight its facet in `pipeline/recommend.py:load_taste_facets` by `min(1, n / min_photos)` with a configurable minimum; verify a test that a one-photo trip is down-weighted/omitted and a well-supported trip keeps full weight.

## 3. Hosted enrichment as a cached chain stage

- [ ] 3.1 Add a `models/` seam that derives structured per-trip attributes and a richer destination description; add the user-scoped `taste_enrichment` cache table via an additive `db._migrate` change; verify a test with an injected stub that results are cached and reused without a second model call.
- [ ] 3.2 Wire the enrichment stage into the pipeline as default-on when a key is configured, with a local deterministic fallback; verify a test that a missing/failed model uses the fallback and the run still completes.
- [ ] 3.3 Feed structured attributes into `destination_text` so the embedding input is richer; verify a test that a destination with attributes embeds/ranks differently from its name-and-country-only form.
- [ ] 3.4 Confirm the privacy boundary: verify a test that only sampled photos/derived text — never the full archive — reach the enrichment seam, and that `core/` still imports no external runtime (existing boundary test stays green).

## 4. Recalibrated blend and embedding discrimination

- [ ] 4.1 Lower the default `alpha` (target ~0.25) and expose it via config/CLI; verify a test for the new default and for a CLI override being honored.
- [ ] 4.2 Keep facets L2-normalized and make the embedding term discriminate; verify a test that, with equal attributes, the candidate closer to the taste embedding ranks higher and no single facet dominates by magnitude.

## 5. Synthetic evaluation gallery and metrics

- [ ] 5.1 Add a pure, deterministic synthetic-gallery generator (trips with known coordinates, counts, and attributes plus known relevant destinations); verify a test that two generations are byte-for-byte identical.
- [ ] 5.2 Add `precision_at_k` and `mrr` to `core/evaluate.py`; verify tests for a perfect ranking, a partial ranking, and an empty relevant set (worst values, no error).
- [ ] 5.3 Add an evaluation path that ranks against the synthetic gallery and reports precision@k / MRR; use it to calibrate `alpha` and the facet threshold, and verify the harness runs green and the chosen defaults are recorded.

## 6. Documentation and full verification

- [ ] 6.1 Update `README.md`/`AGENTS.md` for the enriched pipeline, the `alpha` default change, and the synthetic `eval`; verify the documented command runs.
- [ ] 6.2 Run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
