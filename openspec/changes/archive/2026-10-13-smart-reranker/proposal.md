# Proposal

## Why

From `docs/IMPROVEMENT_PLAN.md` (A8): the seams for an LLM layer already exist
(`HostedRanker`), but nothing turns it on. Rather than a mandatory step, expose it
as an **opt-in** re-ranker over the final shortlist, gated on the metrics.

## What Changes

- **Opt-in re-ranker.** `recommend --rerank` (needs a key) passes a pinned
  `HostedRanker` over the final recommendations, which reorders them and writes a
  grounded one-sentence reason each; without it, ranking is unchanged.
- Off by default; the deterministic path and explanations remain the fallback.
- No **BREAKING** changes.

## Capabilities

### Modified Capabilities
- `recommendation`: an optional hosted re-ranker over the final recommendations.

## Impact

- `wanderlens/cli/main.py`, `wanderlens/pipeline/recommend.py` (already accepts a
  `ranker`).
- Tests for the flag and the existing ranker path.
