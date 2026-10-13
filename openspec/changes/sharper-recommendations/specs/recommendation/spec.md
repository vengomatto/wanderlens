# Spec Delta

## ADDED Requirements

### Requirement: Diversify the ranked list

The system SHALL select the returned Recommendations so they are both high-scoring
and mutually dissimilar, rather than the independently highest-scoring items,
using a tunable diversity weight.

#### Scenario: Near-duplicates avoided

- **WHEN** several top-scoring candidate Destinations are very similar to each other
- **THEN** the list includes dissimilar alternatives instead of only the near-duplicates

#### Scenario: Deterministic

- **WHEN** the same inputs are ranked twice with the same diversity weight
- **THEN** the selected list is identical

### Requirement: Novelty preference biases selection

The system SHALL accept a novelty preference — familiar, balanced, or uncommon —
and bias selection toward well-known or less-known Destinations accordingly.

#### Scenario: Familiar preference

- **WHEN** the preference is familiar and a popular destination and an obscure one are otherwise comparable
- **THEN** the popular destination is preferred

#### Scenario: Uncommon preference

- **WHEN** the preference is uncommon and a popular destination and an obscure one are otherwise comparable
- **THEN** the obscure destination is preferred

#### Scenario: Balanced preference

- **WHEN** the preference is balanced
- **THEN** selection does not favour popularity either way
