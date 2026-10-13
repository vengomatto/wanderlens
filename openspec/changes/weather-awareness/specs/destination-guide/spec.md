# Spec Delta

## ADDED Requirements

### Requirement: Best months and climate match
The system SHALL compute, for a Destination, its best months relative to the
user's climate preference and a climate-match score, cached, and MUST NOT fail
the run when climate data is unavailable.

#### Scenario: Best months computed
- **WHEN** a Destination has monthly climate and the user has a climate preference
- **THEN** its best months and a climate-match score are computed and cached

#### Scenario: No preference
- **WHEN** the user has no climate preference
- **THEN** no best months or climate match are produced for the Destination

#### Scenario: Failure tolerated
- **WHEN** climate data is unavailable for a Destination
- **THEN** it is stored without best months and the run continues
