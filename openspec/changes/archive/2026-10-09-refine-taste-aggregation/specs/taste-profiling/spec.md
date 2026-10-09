# Spec Delta

## ADDED Requirements

### Requirement: Store subjects per trip
The system SHALL record the attributes derived for each trip, so preference can
be measured across trips rather than accumulated globally.

#### Scenario: Per-trip attributes recorded
- **WHEN** a trip is tagged
- **THEN** its canonical attributes are stored against that trip

### Requirement: Weight attributes by trip recurrence
The system SHALL weight each canonical attribute by the proportion of trips in
which it appears, not by the number of photos or tag occurrences.

#### Scenario: Recurring attribute outweighs a one-off
- **WHEN** an attribute appears in several trips and another appears in one
- **THEN** the recurring attribute has the higher weight

#### Scenario: A large album does not dominate
- **WHEN** one trip has far more photos than another
- **THEN** each trip contributes equally to the attribute weights

### Requirement: Per-trip taste facets
The system SHALL represent taste as a set of per-trip facets (one visual centroid
per trip) rather than a single global mean, so adding trips does not flatten the
profile.

#### Scenario: Facets preserved
- **WHEN** the profile is built from several trips
- **THEN** each trip contributes its own facet to the profile
