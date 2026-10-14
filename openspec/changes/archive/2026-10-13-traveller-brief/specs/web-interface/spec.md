# Spec Delta

## ADDED Requirements

### Requirement: Trip brief panel
The web layer SHALL show the user's trip brief on the taste page and SHALL allow
editing it, from local data only.

#### Scenario: Brief shown
- **WHEN** the taste page is rendered
- **THEN** the current trip brief is shown

#### Scenario: Brief edited
- **WHEN** the user saves the brief form
- **THEN** the values are stored and reflected on the next render
