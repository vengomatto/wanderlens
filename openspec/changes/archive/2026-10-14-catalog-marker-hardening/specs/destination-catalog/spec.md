# Spec Delta

## MODIFIED Requirements

### Requirement: Clean marker values
The system SHALL strip wiki markup from a parsed marker/listing `name` — link
brackets (even when the link is unclosed), an optional display alias, and any
`#fragment` — before it becomes a title, id, or lookup key, so names and ids are
clean.

#### Scenario: Bracketed name cleaned
- **WHEN** a marker's name is given as `[[Rome]]` or `[[Rome|Roma]]`
- **THEN** the resulting title is `Rome` or `Roma` respectively

#### Scenario: Unclosed link cleaned
- **WHEN** a marker's name is given as an unclosed link such as `[[Sintra`
- **THEN** the resulting title is `Sintra`
