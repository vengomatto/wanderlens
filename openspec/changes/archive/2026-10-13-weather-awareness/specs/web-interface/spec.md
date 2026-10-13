# Spec Delta

## ADDED Requirements

### Requirement: Show climate fit
The web layer SHALL show, on the destination page, the Destination's best months
and climate-match score when available, from cached data only.

#### Scenario: Climate fit shown
- **WHEN** a Destination has best months or a climate match stored
- **THEN** the destination page shows them

#### Scenario: No climate fit
- **WHEN** no best months or climate match are stored
- **THEN** the section is omitted and the page still renders
