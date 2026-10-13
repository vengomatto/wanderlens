# Spec Delta

## ADDED Requirements

### Requirement: Ranking consumes feedback
The system SHALL incorporate the user's recorded feedback into ranking, applying
a deterministic bias per Destination and leaving ranking unchanged when no
feedback exists.

#### Scenario: Feedback applied
- **WHEN** a Destination has recorded feedback and rankings are produced
- **THEN** its score reflects the feedback bias

#### Scenario: No feedback, no change
- **WHEN** no feedback exists
- **THEN** the ranking matches the feedback-free ranking
