# Design

## Context

See `proposal.md`; behavior in `specs/recommendation/spec.md`,
`specs/destination-popularity/spec.md`, `specs/web-interface/spec.md`.

`rank_destinations` scores each candidate independently and returns the top-k, so
similar candidates cluster at the top. Destination embeddings are already cached
(`destination_embeddings`) and passed to ranking as `vectors`. The web layer
already reads persisted recommendation columns, so popularity can ride along.

## Goals / Non-Goals

**Goals:**

- A varied, non-repetitive list; a fame/novelty signal; deterministic and cheap.
- Keep the deterministic core the default; popularity is best-effort.

**Non-Goals:**

- No learned ranking model or click feedback (later change).
- No change to exclusion, scoring formula, or explanation.

## Decisions

### Diversify with MMR

After scoring, do a greedy Maximal Marginal Relevance selection over the candidate
embeddings:

- pick the highest adjusted score, then repeatedly pick the destination
  maximizing `score - λ · max(cosine to already-selected)`.
- `λ` (`diversity`, default 0.25, range 0–1) trades relevance for variety;
  `λ = 0` is the old behaviour.
- Ties break by name, so selection stays deterministic. Similarity uses the
  destination vectors already supplied to ranking; a missing vector counts as
  dissimilar (0).

*Alternative:* a hard per-country cap. Rejected — MMR is smoother and uses the
taste geometry, not a proxy.

### Popularity from Wikimedia pageviews

`catalog/popularity.py` sums the last 12 months of Wikipedia pageviews for the
Destination's article (free, keyless, with a `User-Agent`) and normalizes:
`score = min(1, log10(total + 1) / 6)`. Classification: `famous` ≥ 0.66,
`uncommon` ≤ 0.33, else `balanced`. Cached in a catalog-scoped
`destination_popularity(destination_id, pageviews, score, fetched_at)` table,
with negative results recorded so a miss is not retried.

### Novelty preference is a small score bias

`novelty ∈ {familiar, balanced, uncommon}` adds `±w · (score − 0.5)` to each
candidate's score before MMR (`w` small, e.g. 0.15); `balanced` is a no-op. This
keeps it deterministic and avoids hard filters that could empty the list.

### Fetch during recommendations, persist on the row

`run_recommend` fetches popularity for the recommended Destinations best-effort
(injectable, like media; a `--no-media`-style flag / `popularity` parameter keeps
tests hermetic), then stores `popularity` and `popularity_label` on the
recommendation rows so the web shows the label offline.

## Risks / Trade-offs

- **MMR can drop a slightly better near-duplicate** → intended; `--diversity 0`
  restores pure relevance.
- **Pageviews are a coarse fame proxy** → acceptable; it only drives a label and a
  mild novelty bias, not the core score.
- **Extra network per destination** → one request, cached once, best-effort;
  failure just omits popularity.
- **Article-title mismatch** → use the Destination name; a miss yields no
  popularity rather than a wrong score.

## Migration Plan

1. Additive `destination_popularity` table and two recommendation columns via
   `db._migrate`.
2. Old rows show no label until the next `recommend`.
3. Rollback: removing the label/flags leaves ranking and schema untouched.

## Open Questions

- `λ` default (0.25) and bias weight (0.15) — tune at implementation.
- Popularity thresholds (0.33 / 0.66) — cosmetic.
