# Proposal

## Why

From `docs/IMPROVEMENT_PLAN.md` (D3/D1, E0/E1): the recommendations page is a
list of rows (dense, low imagery) and liked/saved places are recorded but never
viewable. This is the first, lowest-risk slice of the UI workstream.

## What Changes

- **Explore grid.** The recommendations page gets an image-tile **grid** view
  (with a list/grid toggle), so photos lead instead of a debug-style row.
- **Saved page.** A new `/saved` board lists the places you liked or saved, with
  their reason, from cached data only.
- **Navigation.** A "Saved" link is added to the top bar.
- No **BREAKING** changes.

## Capabilities

### Modified Capabilities
- `web-interface`: an Explore grid view and a Saved board.

## Impact

- `wanderlens/web/views.py`: a `saved_view`.
- `wanderlens/web/app.py`: `GET /saved`.
- `wanderlens/web/templates/`: `saved.html`, `base.html`, `recommendations.html`.
- `wanderlens/web/static/app.css`: grid + tile styles.
- Tests for the grid render and the saved board.
