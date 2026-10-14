# Spec Delta

## ADDED Requirements

### Requirement: Feedback reasons
The system SHALL capture an optional reason for a negative feedback action and
keep it with the action.

#### Scenario: Reason recorded
- **WHEN** a negative action is recorded with a reason
- **THEN** the reason is stored alongside the action

### Requirement: Learned taste bias
The system SHALL derive, per user, a deterministic adjustment vector from liked
versus disliked destinations, and SHALL be able to apply it to ranking.

#### Scenario: Bias derived
- **WHEN** a user has liked and disliked destinations
- **THEN** an adjustment vector is derived from their vectors

#### Scenario: Deterministic
- **WHEN** the same feedback is present
- **THEN** the same adjustment vector is derived
