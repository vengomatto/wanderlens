# Spec Delta

## MODIFIED Requirements

### Requirement: Deterministic POI-based itinerary
The system SHALL build a day-by-day itinerary from the Destination's own points
of interest when no model is available, grouping the points into days **by
geographic proximity** so a day stays in one area, falling back to a simple split
when coordinates are missing.

#### Scenario: Itinerary without a key
- **WHEN** a guide is built with no model configured and the Destination has points of interest
- **THEN** a day-by-day itinerary is derived from those points and stored

#### Scenario: Points grouped by area
- **WHEN** the points of interest form distinct nearby clusters
- **THEN** each day's points come from the same cluster

#### Scenario: No points, no itinerary
- **WHEN** the Destination has no usable points of interest and no model
- **THEN** no synthetic itinerary is stored and the guide remains usable
