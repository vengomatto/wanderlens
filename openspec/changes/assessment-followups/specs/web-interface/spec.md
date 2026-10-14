# Spec Delta

## ADDED Requirements

### Requirement: Every mutating POST requires the token
The web layer SHALL require the per-process token on every mutating POST —
feedback, brief, and jobs — so a page opened elsewhere cannot submit forms while
the dashboard runs.

#### Scenario: Feedback without token
- **WHEN** a feedback POST arrives without the correct token
- **THEN** it is rejected

#### Scenario: Brief without token
- **WHEN** a brief POST arrives without the correct token
- **THEN** it is rejected

### Requirement: The Explore grid does not overflow
The web layer SHALL render the Explore grid and its toolbar without horizontal
overflow at a phone width.

#### Scenario: Phone width
- **WHEN** the Explore page is rendered at a phone width
- **THEN** it does not scroll horizontally
