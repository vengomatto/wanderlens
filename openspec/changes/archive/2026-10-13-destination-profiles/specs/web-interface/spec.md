# Spec Delta

## ADDED Requirements

### Requirement: Show the destination profile
The web layer SHALL show a Destination's structured profile — vibe chips and
suitability fields, with model-estimated fields marked — on the destination page,
from cached data only.

#### Scenario: Profile shown
- **WHEN** a Destination has a stored profile
- **THEN** its vibe chips and suitability fields are shown, with estimated fields labelled

#### Scenario: No profile
- **WHEN** no profile is stored
- **THEN** the section is omitted and the page still renders
