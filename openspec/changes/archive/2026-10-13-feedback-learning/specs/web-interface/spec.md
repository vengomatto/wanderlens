# Spec Delta

## ADDED Requirements

### Requirement: Feedback reasons and run delta
The web layer SHALL offer reason chips with negative feedback and SHALL indicate
which recommendations are new since the previous run.

#### Scenario: Reason chips
- **WHEN** the user gives negative feedback
- **THEN** reason options are offered and the chosen reason is stored

#### Scenario: New since last run
- **WHEN** a recommendation did not appear in the previous run
- **THEN** it is marked as new
