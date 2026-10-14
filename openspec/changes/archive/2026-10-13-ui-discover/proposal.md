# Proposal

## Why

From `docs/IMPROVEMENT_PLAN.md` (E3): a card stack ("Discover") lets the user
quickly react to candidates — like/save/skip/not-for-me — producing labelled
feedback and a fun entry point, using the feedback plumbing that already exists.

## What Changes

- **Discover page.** A swipe/arrow-card stack of current candidates that have no
  feedback yet, with four actions wired to the existing feedback endpoint; the
  stack advances in place (Alpine), with keyboard arrows on desktop.
- **Navigation.** A "Discover" link in the top bar.
- No **BREAKING** changes.

## Capabilities

### Modified Capabilities
- `web-interface`: a Discover triage stack.

## Impact

- `wanderlens/web/views.py`: a `discover_view`.
- `wanderlens/web/app.py`: `GET /discover`.
- `wanderlens/web/templates/`: `discover.html`, `base.html`.
- `wanderlens/web/static/app.css`.
- Tests for the render and the filtering of already-rated candidates.
