# Design

## Context

See proposal.md — Why. The Malta taste profile's subject tags are good, but
ranking ignores them: it uses only `cosine(taste_mean, destination_text_embedding)`,
and both sides are near-generic, so scores cluster within 0.01.

## Goals / Non-Goals

**Goals:**
- Make ranking discriminate on the signal we already extracted (subject tags).
- Keep it deterministic and inspectable.
- No new external dependencies or model downloads.

**Non-Goals:**
- Retraining/replacing CLIP, or learning weights from feedback.
- Fixing the taste vector's granularity (per-trip centroids) — deferred.
- A full place-attribute ontology.

## Decisions

**Reuse the shared attribute vocabulary as the join.** Canonicalize the Taste
Profile's subject tags into weighted attributes, and canonicalize each
Destination's text (`name + description + attributes`) into an attribute set. The
vocabulary already exists to bridge photo tags and catalog text.

**Aggregate profile tags per canonical attribute, normalized.** Sum subject
weights per canonical attribute and normalize to sum 1, so the attribute score is
a 0–1 match fraction independent of tag count.

**Combined linear score.** `score = alpha * embedding_cosine + (1 - alpha) *
attribute_match`, where `attribute_match = sum(taste_weight[a] for a in
destination_attributes)`. Default `alpha = 0.5`, configurable per call.
*Alternatives:* attribute-only (rejected: discards visual nuance); embeddings-only
(rejected: the status quo); learned weighting (deferred: no labels).

**Expose components.** `Recommendation` carries `embedding_score` and
`attribute_score` so we can see which term drove a pick.

## Risks / Trade-offs

- **Vocabulary coverage is thin** → unmatched attributes simply contribute 0;
  ranking degrades to embeddings, never errors.
- **Description false positives** (e.g. "Costa" matching "coast") → synonyms are
  curated substrings; acceptable for v1.
- **`alpha` sensitivity** → kept as a parameter so it can be tuned without a
  code change; integration run reports the effect.
