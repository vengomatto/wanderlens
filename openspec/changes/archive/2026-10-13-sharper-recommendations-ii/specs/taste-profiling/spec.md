# Spec Delta

## MODIFIED Requirements

### Requirement: Group photos into trips
The system SHALL group Photos into trips using configurable capture-time gap and
GPS-proximity thresholds, so split boundaries can be tuned per archive.

#### Scenario: Same trip
- **WHEN** photos are captured within a short time window at nearby coordinates
- **THEN** they are grouped into one trip

#### Scenario: Separate trips
- **WHEN** a capture-time gap or a large spatial jump separates photo groups
- **THEN** the groups form separate trips

#### Scenario: Configurable boundaries
- **WHEN** the capture-time gap or spatial-jump thresholds are configured
- **THEN** trips are split according to those configured values

## ADDED Requirements

### Requirement: Robust taste facets
The system SHALL require a minimum number of Photos for a trip to contribute a
full-weight taste facet; a trip below the threshold contributes a weighted-down
or omitted facet so a one-photo trip does not act as a robust centroid.

#### Scenario: Well-supported trip facet
- **WHEN** a trip has at least the minimum number of Photos
- **THEN** it contributes a full-weight facet

#### Scenario: Thin trip facet
- **WHEN** a trip has fewer Photos than the minimum
- **THEN** its facet is weighted down or omitted rather than treated as a robust centroid
