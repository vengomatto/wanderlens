# Proposal

## Why

From `docs/IMPROVEMENT_PLAN.md` (D7): the overview map shows plain dots with no
way to reach a place, and a destination's approximate area can render at world
scale. Small, high-visibility fixes.

## What Changes

- **Link map markers.** Overview-map markers carry a link to the destination or
  trip page, so a dot is a door.
- **Fit the region.** The destination region map fits to the drawn area (polygon
  or approximate circle) so an approximate place is not shown at world scale.
- No **BREAKING** changes.

## Capabilities

### Modified Capabilities
- `web-interface`: map markers link to their pages; the region map fits its area.

## Impact

- `wanderlens/web/views.py`: `MapPoint.url`.
- `wanderlens/web/app.py`: include the url in the payload.
- `wanderlens/web/static/map.js`, `destination.js`.
- Tests for the payload urls.
