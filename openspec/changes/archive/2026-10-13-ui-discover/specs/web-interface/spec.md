# Spec Delta

## ADDED Requirements

### Requirement: Discover triage stack
The web layer SHALL present a card stack of current candidates that have no
feedback yet, and SHALL let the user react (like, save, skip, dislike) with the
actions recorded and the stack advancing in place.

#### Scenario: Stack shown
- **WHEN** the Discover page is rendered
- **THEN** candidates without feedback are shown one at a time

#### Scenario: Reacting advances
- **WHEN** the user activates an action on the current card
- **THEN** the action is recorded and the next candidate is shown

#### Scenario: Everything rated
- **WHEN** every candidate already has feedback
- **THEN** the page shows an empty state
