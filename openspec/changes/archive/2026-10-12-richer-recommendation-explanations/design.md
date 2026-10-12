# Design

## Context

See `proposal.md`; the behavior contract is in
`specs/recommendation/spec.md` and `specs/web-interface/spec.md`.

Current state that shapes the approach:

- `rank_destinations` (`core/recommend.py`) already scores destinations against
  per-trip facets: `embedding_score = max(dot(facet, vector) for facet in
  facets)`. The winning facet is computed but its Trip is discarded.
- `_attribute_match` returns a single float; the matched attributes are not kept.
- `Recommendation` carries `embedding_score` and `attribute_score`; the
  `recommendations` table persists display fields and score components.
- `run_recommend` already accepts an injectable `ranker`; `models/llm.py` holds
  the only LLM HTTP (`HostedTextModel`), and AGENTS confines model/LLM HTTP to
  `models/`.

## Goals / Non-Goals

**Goals:**

- Turn the fixed explanation into something specific and true to the profile:
  which trip, which recurring attributes, how novel.
- Keep the deterministic core the default and the LLM an optional, cached,
  injectable layer.
- Persist the evidence so the web renders it without recomputation and offline.

**Non-Goals:**

- Changing the ranking order (this change adds evidence, it does not re-weight).
- Traveller-context questions or itinerary synthesis (separate changes).
- Free-text generation without grounding: the LLM only rewrites given facts.

## Decisions

### Facets carry their Trip identity

Introduce `Facet(trip_id, label, vector)` in `core/models.py`.
`load_taste_facets` returns facets; `rank_destinations` accepts a sequence whose
items are `Facet` or a bare vector (wrapped as an anonymous facet, keeping
existing callers and tests working). The strongest facet's `trip_id`/`label` and
its similarity are recorded on the Recommendation.

*Alternative:* keep anonymous vectors and map back by index. Rejected — fragile;
identity belongs to the facet.

### Matched attributes are reported, not just summed

Split `_attribute_match` into `matched_attributes(taste_weights, destination) ->
dict[str, float]`; `attribute_score` becomes `sum(values)` exactly as before, so
scoring is unchanged. The matched attributes are carried on the Recommendation.

### Novelty is the nearest visited distance

Compute `nearest_visited_km(destination, centers)` (haversine). Because candidates
are already filtered to be outside the exclusion radius, this is always `>
radius`, but the exact figure lets the explanation say "new for you" factually.

### Evidence is persisted on the Recommendation

Additive columns on `recommendations`: `matched_attributes` (JSON),
`best_trip_id`, `best_trip_label`, `best_facet_similarity`, `nearest_trip_km`,
applied in `db._migrate` (same pattern as the existing additive columns).

### Deterministic `explain(evidence)` is the default

Rewrite `explain` to build the sentence from the evidence:
closest trip ("closest to your *Puglia 2022* trip"), the recurring attributes
("shares coastal (4/6 trips), hiking (3/6)"), and novelty ("new — no visit within
60 km"). No evidence falls back to a short generic line. Deterministic and
repeatable.

### Synthesis is an injectable port, cached by evidence

Add `ExplanationSynthesizer` to `core/ports.py` (Protocol only). The default
implementation lives in `models/` and uses `HostedTextModel` with a **pinned
model id and prompt version**; it receives the evidence as JSON and returns two
or three sentences. `run_recommend(..., explainer=None)` uses the deterministic
`explain` unless an explainer is supplied (CLI wires the default when an API key
and the feature flag are present).

Synthesis is cached in `recommendation_explanations(user_id, destination_id,
evidence_hash, model, prompt_version, text, created_at)`, where `evidence_hash`
is a stable hash of the facts. Re-running with the same evidence reuses the text,
so the smart layer stays reproducible. Any error falls back to the deterministic
explanation and never fails the run.

*Alternative:* generate fresh every run. Rejected — non-reproducible and costs
money; caching by evidence makes it deterministic after the first run.

### The web shows the evidence

`RecView`/`DestinationDetail` gain the closest trip and matched attributes; the
destination page renders shared-attribute chips and a "closest to your …" line,
reading only from storage (no model, no network).

## Risks / Trade-offs

- **LLM hallucination** → the prompt receives only the computed facts and is
  asked to rewrite, not invent; output is short and cached; deterministic
  fallback always available.
- **Cache key drift** → `evidence_hash` covers every fact fed to the model; a
  prompt-version bump invalidates deliberately.
- **Ranking regression** → order must not change; a test asserts identical
  ordering with and without the new evidence.
- **Score drift** → `attribute_score` is still the sum of the matched weights;
  tests pin the value.
- **Facet API churn** → `rank_destinations` accepts bare vectors, so existing
  tests keep passing.

## Migration Plan

1. Additive `ALTER TABLE recommendations` columns + `recommendation_explanations`
   table via `db._migrate` (idempotent).
2. Old rows render with the explanation and no chips until the next `recommend`.
3. Rollback: removing the web chips and the explainer leaves ranking, CLI, and
   schema untouched.

## Open Questions

- Exact wording/phrasing of the deterministic template and how many attributes
  to name (propose top three by recurrence) — cosmetic.
- Whether to expose the synthesis feature flag as `--explain-llm` or an env var —
  decide at implementation; does not change the approach.
