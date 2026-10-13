# Design

## Context

See `proposal.md` for motivation and `specs/*/spec.md` for the behavior contracts.

Current state that shapes the approach:

- `core/recommend.py:rank_destinations` blends `alpha * embedding_score +
  (1 - alpha) * attribute_score` with `alpha = 0.5` (default). On the real
  archive the embedding term is nearly constant, so half the score is wasted.
- `core/vocabulary.py:canonicalize` matches synonyms with Python `in`
  (substring), so `"art"` matches `"earth"`; there is no notion of how
  informative a match is.
- `pipeline/recommend.py:load_taste_facets` averages every trip's photo vectors
  with no minimum-count guard, so a one-photo trip yields a "centroid" equal to
  that photo.
- `core/taste.py:cluster_into_trips` hard-codes `18h` / `150km`.
- `models/` already hosts the only allowed LLM/VLM HTTP calls behind injectable
  seams (`HostedVLM`, `HostedRanker`, `HostedExplanationSynthesizer`) with
  evidence-hash caching in `recommendation_explanations`.
- `core/evaluate.py` only checks whether a hold-out resurfaces; there are no
  aggregate quality metrics and the only archive is tiny.

Constraints: `core/` imports no external runtime; hosted-model traffic stays in
`models/`; ranking must be deterministic for identical inputs; persisted rows are
user-scoped.

## Goals / Non-Goals

**Goals:**

- Make the embedding signal carry weight by enriching the text it is computed
  from, and blends it at a calibrated ratio.
- Make attribute matching correct (word-boundary) and information-aware (IDF).
- Make facets robust to thin trips and splitting tunable.
- Make quality **measurable** with a reproducible synthetic gallery and
  precision@k / MRR.

**Non-Goals:**

- No change to the ports/adapters boundaries or to the exclusion logic.
- The hosted model is **not** made a mandatory ranking judge; the deterministic
  core still decides the order.
- No catalog-name/granularity cleanup (separate concern), no feedback loop, no
  learned ranker.

## Decisions

### Robust facets: down-weight, don't drop

`load_taste_facets` records each trip's photo count. A facet's weight is
`min(1, n / min_photos)` with `min_photos` configurable (default ~4); a trip's
facet is omitted only below an absolute floor (default 1 means omit nothing but
weight near-zero). Facet weights multiply into the facet's contribution.

*Alternative:* drop thin trips entirely — rejected, it throws away the only
signal some archives have. Down-weighting degrades gracefully and the synthetic
gallery measures both.

### Configurable splitting, defaults preserved

`cluster_into_trips` takes `max_gap` / `max_jump_km` from config instead of
constants. Defaults stay `18h` / `150km`, so existing behavior is unchanged until
tuned; the synthetic gallery is the tuning harness.

*Alternative:* pick a new default (e.g. `36h`) now — rejected without data.

### Hosted enrichment as a cached chain stage, not a fallback

Add a `models/` seam (e.g. `HostedTasteEnricher`) with two operations: turn a
trip's photo tags + context into **structured canonical attributes**, and turn a
thin Destination into a **richer description**. The pipeline runs it as a normal
stage (default-on when an API key is configured), caching results in a new
user-scoped `taste_enrichment` table keyed by `(kind, input_hash, model,
prompt_version)` — the same reproducibility pattern as explanation caching. A
local deterministic representation is the fallback, and any model error is
swallowed so the run continues.

Rationale: the LLM transforms **inputs** (cached, reproducible) rather than
judging the final order, which unblocks the embedding term without sacrificing
determinism or hermetic tests (tests inject a deterministic stub).

*Alternative:* make `HostedRanker` a mandatory chain step — rejected: it is
nondeterministic, hard to test, and the flat signal it would compensate for is
better fixed at the source.

### Word-boundary matching and IDF specificity

Tokenize on non-word boundaries and match whole tokens (multi-word synonyms like
"old town" matched as a token sequence), removing substring false positives.
Weight each matched attribute by an IDF term computed over the candidate catalog
(`log(N / (1 + df))`, deterministic for a given catalog) times its recurrence
weight, so rare, descriptive attributes outrank generic ones. Expand the
vocabulary where obviously thin.

*Alternative:* keep recurrence-only weights — rejected; it is exactly what makes
`hiking 0.83` from a handful of photos dominate.

### Recalibrated blend

Lower the default `alpha` (target ~0.25, exposed via config/CLI) now that the
embedding input is richer, and keep facets L2-normalized so no facet dominates by
magnitude. The value is chosen by the synthetic-gallery metrics, not guessed in
the spec.

### Synthetic gallery and metrics

Add a pure generator (e.g. `core/gallery.py`) that deterministically produces
trips with known coordinates, counts, and attributes, plus known relevant
destinations. Metrics `precision_at_k` and `mrr` live in `core/evaluate.py`
alongside the existing hold-out check and are exercised by tests and a
`eval --synthetic` path.

*Alternative:* tests-only inline fixtures — rejected; a reusable core module lets
the CLI and future CI use the same corpus.

## Risks / Trade-offs

- **Model nondeterminism / cost** → cached by input+model+prompt, pinned model,
  injected stub in tests; deterministic fallback.
- **IDF unstable on a 207-destination catalog** → compute over the actual
  candidate set at rank time; identical catalog yields identical weights.
- **Down-weighting thin trips may shrink signal on tiny archives** → weight
  floor, plus the synthetic gallery guards against regression.
- **Configurable split could change results if defaults drift** → defaults pinned
  to today's constants; tests assert default behavior is unchanged.
- **New user-scoped tables/columns** → additive migration in `db._migrate`, no
  destructive change.

## Migration Plan

1. Additive `taste_enrichment` table (user-scoped) and any attribute columns via
   `_migrate`.
2. Enrichment and enrichment-derived text are best-effort; absent data falls back
   to current behavior.
3. `alpha` default change is observable: document it in `README.md` and keep it
   overridable via CLI.
4. Rollback: revert the `alpha` default and ignore the enrichment table; ranking
   and schema remain valid.

## Open Questions

- Exact `min_photos`, the facet-weight floor, and the `alpha` default — tuned at
  implementation against the synthetic gallery, not load-bearing for the specs.
- Whether the split defaults should change once the gallery can compare settings
  — deferred.
