# Spec Delta

## ADDED Requirements

### Requirement: Trips record their location
The system SHALL record a location (centroid) for each trip, derived from its
geotagged photos, so visited areas can be compared spatially.

#### Scenario: Centroid recorded
- **WHEN** a trip contains geotagged photos
- **THEN** the trip stores a latitude and longitude centroid

#### Scenario: No geotagged photos
- **WHEN** a trip has no geotagged photos
- **THEN** it records no centroid and contributes no spatial exclusion
