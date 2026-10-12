# Spec Delta

## MODIFIED Requirements

### Requirement: Explore Recommendations

The system SHALL present ranked Recommendations with the destination, the
explanation, and the separate embedding and attribute score components, each
card carrying a representative image where one is available and opening the
destination detail page.

#### Scenario: Recommendation cards

- **WHEN** the user opens the recommendations view
- **THEN** each Recommendation shows its destination, rank, score components, and explanation

#### Scenario: Recommendation card shows a picture

- **WHEN** a Recommendation has cached media
- **THEN** its card shows a representative image, or a placeholder when none exists

#### Scenario: Recommendation opens its page

- **WHEN** the user activates a Recommendation card
- **THEN** the destination detail page opens

## ADDED Requirements

### Requirement: Destination detail page

The system SHALL provide a page per Destination presenting its images, expanded
description, source link and attribution, its location, and why it matches the
Taste Profile.

#### Scenario: Detail page content

- **WHEN** the user opens a destination page that has cached media
- **THEN** it shows the images, the expanded description, the source link, and why it matches

#### Scenario: Missing media degrades gracefully

- **WHEN** a destination page has no cached media
- **THEN** it still renders with a placeholder, the short description, and location

### Requirement: Locate a destination on the world

The system SHALL show, on the destination page, a world locator and a regional
map, highlighting the destination's area when a region geometry is available,
and labelling an approximate area as approximate.

#### Scenario: Region highlighted

- **WHEN** a region geometry is available
- **THEN** the regional map draws the destination's area and the world locator marks its position

#### Scenario: Approximate area labelled

- **WHEN** the region geometry is approximate
- **THEN** the map labels the highlighted area as approximate

#### Scenario: No geometry

- **WHEN** no region geometry is available
- **THEN** the map shows the destination marker only

### Requirement: Similar-visit evidence

The system SHALL show, on the destination page, the user's own Trip photos whose
taste is closest to the destination.

#### Scenario: Similar visits shown

- **WHEN** the user has visited places whose taste resembles the destination
- **THEN** their photos appear as evidence on the destination page

#### Scenario: No similar visits

- **WHEN** no visited trip resembles the destination
- **THEN** the similar-visits section is omitted
