# Spec Delta

## ADDED Requirements

### Requirement: Famous or uncommon label

The system SHALL show, on the recommendation card and the destination page, a
label indicating whether the Destination is famous, balanced, or uncommon.

#### Scenario: Label shown

- **WHEN** a Recommendation has a popularity score
- **THEN** its card and destination page show a famous, balanced, or uncommon label

#### Scenario: No popularity

- **WHEN** a Recommendation has no popularity score
- **THEN** no label is shown
