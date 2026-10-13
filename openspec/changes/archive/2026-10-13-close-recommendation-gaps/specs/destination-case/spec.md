# Spec Delta

## ADDED Requirements

### Requirement: Case built for the shortlist
The system SHALL build cases for the candidate shortlist, not only the final
recommendations, so a case can inform the choice.

#### Scenario: Shortlist cased
- **WHEN** recommendations are generated
- **THEN** candidates in the shortlist have a case available

### Requirement: Case surfaced on the card
The web layer SHALL show a short case snippet or highlights on the recommendation
card, from cached data only.

#### Scenario: Card shows the case
- **WHEN** a recommendation has a stored case
- **THEN** the card shows a snippet of it and still links to the full page
