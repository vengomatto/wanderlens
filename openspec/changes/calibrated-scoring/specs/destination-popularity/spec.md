# Spec Delta

## ADDED Requirements

### Requirement: Exact-title pageviews
The system SHALL fetch a Destination's pageviews by its exact article title when
the id carries one, falling back to the display name, so ambiguous names do not
hit the wrong article.

#### Scenario: Title from id
- **WHEN** a Destination id carries an article title
- **THEN** pageviews are fetched for that exact title

#### Scenario: Name fallback
- **WHEN** a Destination id carries no title
- **THEN** pageviews are fetched for the display name
