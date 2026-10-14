# feedback Specification

## Purpose

Records a user's explicit reaction to a Destination and biases future
recommendations by it, so taste can improve after ingestion.

## Requirements

### Requirement: Record feedback
The system SHALL record, per user, an action of `save`, `like`, `dislike`, or
`skip` against a Destination, and SHALL keep the latest action per Destination.

#### Scenario: Feedback recorded
- **WHEN** the user marks a Destination as liked, disliked, saved, or skipped
- **THEN** the action is stored for that user and Destination

#### Scenario: Latest action wins
- **WHEN** a Destination already has an action and a new one is recorded
- **THEN** the latest action replaces the earlier one

### Requirement: Feedback biases ranking
The system SHALL bias a Destination's rank by its recorded feedback — favouring
liked and saved, penalising disliked and skipped — deterministically.

#### Scenario: Liked favoured
- **WHEN** two otherwise equal Destinations are ranked and one is liked
- **THEN** the liked Destination ranks above the other

#### Scenario: Disliked penalised
- **WHEN** a Destination is disliked
- **THEN** it is pushed down the ranking

#### Scenario: Deterministic without feedback
- **WHEN** no feedback exists
- **THEN** the ranking is unchanged from the feedback-free ranking

### Requirement: Feedback is inspectable and removable
The system SHALL let the user list and clear recorded feedback.

#### Scenario: List and clear
- **WHEN** the user lists feedback
- **THEN** the recorded actions are shown and can be cleared

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
