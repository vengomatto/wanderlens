# Spec Delta

## ADDED Requirements

### Requirement: Map markers link to their pages
The web layer SHALL give each map marker a link to the destination or trip it
represents, so it can be opened from the map.

#### Scenario: Marker links
- **WHEN** the overview map is rendered
- **THEN** each marker carries a link to its destination or trip page

### Requirement: Region map fits its area
The web layer SHALL fit the destination region map to the drawn area — a polygon
or an approximate circle — so the area is not shown at world scale.

#### Scenario: Approximate area fitted
- **WHEN** a destination's region is an approximate circle
- **THEN** the region map fits that circle rather than the whole world
