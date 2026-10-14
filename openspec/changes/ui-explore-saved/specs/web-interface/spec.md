# Spec Delta

## ADDED Requirements

### Requirement: Explore grid view
The web layer SHALL offer an image-tile grid view of the recommendations, with a
toggle to the list view, so photos lead the page.

#### Scenario: Grid offered
- **WHEN** the recommendations page is rendered
- **THEN** an image-tile grid is available and photos are prominent

#### Scenario: List toggle
- **WHEN** the user switches to list view
- **THEN** the same recommendations are shown as a list

### Requirement: Saved board
The web layer SHALL show a board of the destinations the user liked or saved,
with their recorded reason, from cached data only.

#### Scenario: Saved shown
- **WHEN** the user has liked or saved destinations
- **THEN** the board lists them with their reason

#### Scenario: Empty board
- **WHEN** nothing is liked or saved
- **THEN** the board shows an empty state and the page still renders
