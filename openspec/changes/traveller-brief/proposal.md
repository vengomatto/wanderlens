# Proposal

## Why

From `docs/IMPROVEMENT_PLAN.md` (A6): the ROADMAP says travel happens with a
toddler and wants fewer accommodation changes, but none of that context is used.
A short, editable trip brief lets recommendations respect party, pace, travel
range, budget, and season.

## What Changes

- **Trip brief storage.** A small, per-user brief: party (adults, children),
  pace, season window, maximum travel distance, home location, and budget level,
  editable and reusable.
- **Apply it to recommendations.** Filter candidates beyond the maximum travel
  distance from home, and feed the season into ranking; prefer family-friendly
  destinations when children are present (from profiles when available).
- **CLI and dashboard.** `wanderlens brief` to view/set it, and an editable panel
  on the taste page.
- No **BREAKING** changes; an empty brief changes nothing.

## Capabilities

### New Capabilities
- `traveller-brief`: stores and applies a per-user trip brief.

### Modified Capabilities
- `recommendation`: candidates are filtered by the brief's travel range and use
  its season.
- `web-interface`: the brief is shown and editable on the taste page.

## Impact

- `wanderlens/db.py`: a `traveller_brief` table.
- `wanderlens/pipeline/brief.py`: save/load/apply.
- `wanderlens/pipeline/recommend.py`, `cli/main.py`.
- `wanderlens/web/`: brief panel.
- Tests for storage, the travel filter, and the season hand-off.
