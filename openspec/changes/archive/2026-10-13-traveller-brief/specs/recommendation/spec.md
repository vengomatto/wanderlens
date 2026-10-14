# Spec Delta

## ADDED Requirements

### Requirement: Brief-constrained candidates
The system SHALL, when the trip brief sets a home location and a maximum travel
distance, exclude candidates beyond that distance, and SHALL use the brief's
season for ranking when no season is given explicitly.

#### Scenario: Travel range applied
- **WHEN** a candidate is farther from home than the brief's maximum
- **THEN** it is excluded from the recommendations

#### Scenario: Season hand-off
- **WHEN** the brief has a season and none is passed explicitly
- **THEN** ranking prefers destinations whose best months include it
