# Proposal

## Why

From `docs/IMPROVEMENT_PLAN.md` (A3, L6; A5.2, L11): the final score mixes
incompatible scales (an embedding around 0.1–0.3, an attribute sum that can exceed
1, plus small bias terms), so weights are guesses. And pageviews are fetched by
display name, so ambiguous names ("Arcadia", "Magnesia") hit the wrong article.

## What Changes

- **Per-pool calibration (opt-in).** When enabled, the embedding and attribute
  components are rescaled across the candidate pool before blending, so one term
  cannot dominate by magnitude. Off by default, to be promoted only if
  `eval --loto` improves.
- **Exact-title pageviews.** Fetch pageviews by the exact article title carried on
  the Destination id (`wv:<title>`), falling back to the display name, so the
  popularity signal stops hitting the wrong page.
- No **BREAKING** changes.

## Capabilities

### Modified Capabilities
- `recommendation`: score components can be calibrated per pool.
- `destination-popularity`: pageviews are fetched by exact article title.

## Impact

- `wanderlens/core/recommend.py`: a `calibrate` path over the scored pool.
- `wanderlens/catalog/popularity.py`: `article_title`.
- `wanderlens/pipeline/recommend.py`, `cli/main.py`, `config.py`: wiring/flags.
- Tests for calibration and exact-title lookup.
