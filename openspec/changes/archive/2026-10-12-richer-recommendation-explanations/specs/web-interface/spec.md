# Spec Delta

## ADDED Requirements

### Requirement: Show the evidence behind the match

The system SHALL present, on the destination page, the evidence behind the match
— the closest visited Trip and the shared attributes — in addition to the
explanation.

#### Scenario: Evidence shown

- **WHEN** a destination page has stored match evidence
- **THEN** it shows the closest visited trip and the shared attributes as chips

#### Scenario: No evidence

- **WHEN** a destination page has no match evidence
- **THEN** it shows the explanation alone
