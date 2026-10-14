# Proposal

## Why

From `docs/IMPROVEMENT_PLAN.md` (N1, D8, E0/E2): feedback is a GET link that
writes state and reloads the page (prefetch/crawlers can trigger it), the buttons
have no styling, the page overflows horizontally at 390 px, and every in-app link
does a full page load. These are small, high-visibility fixes.

## What Changes

- **Feedback is a POST that stays put.** The buttons post to a route that writes
  the action and returns the refreshed button group in place (HTMX), with a
  redirect fallback for no-JS. No GET-that-writes, no reload, no history entry.
- **Styled feedback buttons** and an "estimated" badge.
- **Mobile robustness:** no horizontal overflow, wrapping nav, single-column
  destination grid at narrow widths.
- **Boosted navigation:** `hx-boost` on the body so in-app links navigate without
  a full reload.
- **Favicon** so the 404 console error goes away.
- No **BREAKING** changes.

## Capabilities

### Modified Capabilities
- `web-interface`: feedback is a POST returning a fragment; mobile layout does not
  overflow; a favicon is provided; navigation is boosted.

## Impact

- `wanderlens/web/app.py`: the feedback route is a POST returning the fragment.
- `wanderlens/web/templates/`: `_feedback.html`, `base.html`, `destination.html`.
- `wanderlens/web/static/app.css`: feedback/badge styles, mobile fixes.
- Tests for the POST fragment, the redirect fallback, and settings.
