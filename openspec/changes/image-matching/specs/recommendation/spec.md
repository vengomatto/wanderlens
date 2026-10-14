# Spec Delta

## ADDED Requirements

### Requirement: Image-to-image scoring with text fallback
The system SHALL, when a Destination has a visual vector, score it by the best
taste-facet match against that vector, and otherwise fall back to the text
embedding.

#### Scenario: Image vector preferred
- **WHEN** a Destination has a visual vector
- **THEN** its embedding score uses the visual vector

#### Scenario: Text fallback
- **WHEN** a Destination has no visual vector
- **THEN** its embedding score uses the text vector
