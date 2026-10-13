# Spec Delta

## ADDED Requirements

### Requirement: Cases built for the shown recommendations
The system SHALL build a Destination case only for the recommendations that are
returned, not for the whole candidate shortlist, so model and search work is not
wasted on places the user never sees.

#### Scenario: Only shown destinations are cased
- **WHEN** recommendations are generated
- **THEN** cases are built for the returned Destinations only
