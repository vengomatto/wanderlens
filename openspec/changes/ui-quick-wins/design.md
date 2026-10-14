# Design

## Context

See `proposal.md`. The feedback route was a GET returning a redirect; the buttons
were anchors with no CSS. `base.html` has a topbar nav with `hx-boost` only on the
nav; the body has no boost. `app.css` has tokens and a mobile block but the grid
still overflows at 390 px.

## Decisions

### POST + fragment
The route becomes `POST /destinations/{id}/feedback` with the action as a query
param (no body, so no `python-multipart` dependency). It records the action, then
returns the `_feedback.html` partial (rendered with the new state) when the
request is an HTMX request, else a 303 redirect. The buttons are `<button>` with
`hx-post` and `hx-target="closest .feedback" hx-swap="outerHTML"`, so only the
control is replaced. This removes the GET-writes-state problem (N1).

### Shell and CSS
`base.html` gets a data-URI favicon and `hx-boost="true"` with `hx-target="main"`
on the body. `app.css` gains feedback-button and `.estimated` styles, `min-width:0`
on grid children, `overflow-x: hidden` and wrapping nav under 660 px, and a
single-column destination grid. These are additive; the palette is untouched.

## Risks / Trade-offs

- **No-JS fallback** → a normal form/redirect path is kept via the 303 branch.
- **hx-boost on the body** can intercept links that should hard-navigate → the map
  and image routes are unaffected; if a future link needs a full load it can opt
  out with `hx-boost="false"`.
