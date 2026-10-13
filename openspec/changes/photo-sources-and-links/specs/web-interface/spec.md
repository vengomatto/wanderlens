# Spec Delta

## ADDED Requirements

### Requirement: Photo links on the recommendation card
The web layer SHALL offer the outbound photo-search links (Commons, Getty,
Google Images) on the recommendation card, from derived data only.

#### Scenario: Card offers photo links
- **WHEN** a recommendation card is rendered
- **THEN** it offers outbound photo-search links for that Destination

### Requirement: Dedicated More photos section
The destination page SHALL present the outbound photo-search links in a dedicated
"More photos" section, independent of whether a case exists.

#### Scenario: Section always present
- **WHEN** a destination page is rendered
- **THEN** a dedicated More photos section with the outbound links is shown
