# Design

## Context

See `docs/ASSESSMENT.md` 3.3/6. `check_regression(mrr, baseline, margin=0.05)` is
absolute; the job route builds its own `run_recommend` call; feedback/brief POSTs
skip the token; the Grid/List toggle causes overflow.

## Decisions

- **Relative gate:** `check_regression` compares `mrr >= baseline * (1 - margin)`
  (margin 0.1); the baseline is refreshed from a real LOTO run.
- **Shared options:** add `run_recommend_ui(config, user_name, count=8)` that sets
  the CLI defaults (diversity 0.25, case builder, popularity, explainer) and use
  it from the dashboard job, so both paths agree.
- **Token everywhere:** feedback and brief POSTs take the same `token` query
  param and reject a mismatch; templates append `post_token`.
- **Overflow:** `minmax(min(260px, 100%), 1fr)` and a wrapping toolbar.

## Risks / Trade-offs

- **Existing no-token tests** must add the token → updated; the rejection path is
  tested.
