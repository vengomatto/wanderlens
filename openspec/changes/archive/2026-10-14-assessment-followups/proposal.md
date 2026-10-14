# Proposal

## Why

From `docs/ASSESSMENT.md` section 3.3 and section 6: the eval gate cannot fail;
the job POST and the CLI produce different recommendations; feedback and brief
POSTs lack the CSRF token the job routes have; and Explore overflows on a phone.

## What Changes

- **A gate that can fail.** The baseline is refreshed and the check becomes
  relative (fail if MRR drops by more than a percentage of the baseline).
- **UI jobs match the CLI.** A single option set is used by both the CLI and the
  dashboard job so the same button gives the same result.
- **CSRF on every POST.** The feedback and brief POSTs require the same
  per-process token as the job POSTs.
- **No Explore overflow.** The tile grid and toolbar no longer overflow at 390 px.
- No **BREAKING** changes.

## Capabilities

### Modified Capabilities
- `evaluation`: the regression gate compares against a relative margin.
- `web-interface`: all POSTs require the token; the grid is mobile-safe.

## Impact

- `scripts/eval.sh`, `wanderlens/core/evaluate.py`, `docs/eval-baseline.json`.
- `wanderlens/pipeline/recommend.py`, `wanderlens/cli/main.py`, `web/jobs.py`.
- `wanderlens/web/app.py`, templates, `app.css`.
- Tests.
