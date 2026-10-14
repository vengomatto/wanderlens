# Spec Delta

## ADDED Requirements

### Requirement: Old town does not imply a city tag
The system SHALL match `old town` as an old-town attribute without also treating
it as a generic city, so the vocabulary does not over-match `town` inside
`old town`.

#### Scenario: Old town only
- **WHEN** a tag is `old town`
- **THEN** it yields the old-town attribute and not the city attribute
