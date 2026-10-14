# Design

## Context

See `proposal.md`. `run_recommend(..., ranker=None)` already calls
`ranker.rank(recommendations, profile)` when provided, else writes deterministic
explanations. `HostedRanker` (models/ranker.py) is pinned and injectable.

## Decisions

- Add a `--rerank` CLI flag: when set and a key is configured, build
  `HostedRanker` and pass it. Off by default.
- Harden the ranker path so a re-ranker error falls back to the deterministic
  explanations instead of failing the run (the "never fatal" rule).

## Risks / Trade-offs

- **Non-determinism / cost** → opt-in, pinned model, single call over the final N;
  the plan's metric gate governs promotion.
