# Design

## Context

See `proposal.md`. `recommendations_view` returns `RecView`s with `has_image`;
images are served at `/destination-image/{id}/0`. `feedback` stores the action and
(lately) a reason. `base.html` has the top-bar nav with `hx-boost`.

## Decisions

### Grid as a CSS state
Keep one list of cards; the page wraps them in `x-data="{ view: 'grid' }"` and
applies `rec-grid` vs `rec-list` classes with a small toggle. The tiles reuse the
existing card markup (hero image, name, country, reason, badges), so no data
changes and the list view stays available.

### Saved board from feedback
`saved_view(conn, user_id)` selects liked/saved feedback rows, left-joined to the
latest recommendation run for name/country/coords/description, and to
`destination_media`/`destination_images` for a hero. Rows missing from the latest
run still render from their id. `GET /saved` renders `saved.html`.

## Risks / Trade-offs

- **Images may be missing for old saves** → placeholder tile, as elsewhere.
- **The toggle depends on Alpine** (already vendored) → list is the no-JS default
  in markup; grid is applied client-side.
