# Proposal

## Why

From `docs/IMPROVEMENT_PLAN.md` (A7, L12): feedback changes ranking but is never
learned from, the *reason* for a dislike is not captured, impressions are not
logged, and every recommendation run wipes the table (`run_id` is always 1), so
there is no history and no "new since last run".

## What Changes

- **Reasons on feedback.** A dislike/skip can carry a reason chip ("too touristy",
  "too far", "not my vibe", "been there"), stored and shown.
- **Learned taste bias.** A deterministic, per-user adjustment vector is derived
  from liked versus disliked destinations and applied to ranking behind an
  opt-in weight.
- **Run history.** `run_id` increments per run, rows are kept (bounded), and
  readers use the latest run. The UI can mark what is new since the previous run.
- **Impressions.** What was shown and its order is logged per run.
- No **BREAKING** changes; the bias is off by default.

## Capabilities

### Modified Capabilities
- `feedback`: reasons are captured; a learned bias is derived.
- `recommendation`: runs are versioned and impressions logged; an optional
  feedback-bias term.
- `web-interface`: reason chips and a "new since last run" indicator.

## Impact

- `wanderlens/db.py`: `feedback.reason`, an `impressions` table.
- `wanderlens/core/recommend.py`: a `taste_bias` term.
- `wanderlens/pipeline/recommend.py`: run ids, impressions, bias build.
- `wanderlens/web/views.py` + templates, `cli/main.py`.
- Tests for reasons, the bias, run history, and impressions.
