# Design

## Context

See `proposal.md`. `map_points` builds `MapPoint(kind, label, lat, lon)`; the
`/map` route serialises it to `window.__points`. `map.js` binds a plain popup.
`destination.js` builds `bounds` from the point, the precise polygon, and POIs,
then `fitBounds`; the approximate circle is drawn but not added to `bounds`.

## Decisions

- Add `MapPoint.url` and set it in `map_points` (`/trips/{id}` for a trip,
  `/destinations/{urlencoded id}` for a destination); carry it in the payload.
- `map.js` binds `<a href=url>` in the popup.
- `destination.js` adds the approximate circle's `getBounds()` to `bounds`, so
  `fitBounds` fits the area; a lone point already sets a sensible zoom.

## Risks / Trade-offs

- **A full vector map (MapLibre)** is deferred → this keeps Leaflet and vendors
  nothing new; the plan's stack change is a later, larger step.
