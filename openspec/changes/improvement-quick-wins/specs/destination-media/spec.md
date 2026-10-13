# Spec Delta

## ADDED Requirements

### Requirement: Clean, sentence-aware extracts
The system SHALL strip wikitext section headings from a Destination's extract and
cut long text at a sentence boundary, so the shown description is clean prose.

#### Scenario: Headings removed
- **WHEN** an extract contains section markers such as `== Cities ==`
- **THEN** those markers are not shown

#### Scenario: Cut at a sentence
- **WHEN** a description must be shortened
- **THEN** it is cut at a sentence boundary rather than mid-sentence
