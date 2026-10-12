# Spec Delta

## ADDED Requirements

### Requirement: Destination photo gallery

The system SHALL present a gallery of the Destination's cached images on the
destination page, at least ten where available, each with its attribution.

#### Scenario: Gallery shown

- **WHEN** a destination page has cached images
- **THEN** they are shown as a gallery

#### Scenario: No images

- **WHEN** a destination page has no cached images
- **THEN** the gallery is omitted

### Requirement: Reading list

The system SHALL present, on the destination page, books and novels set in or
about the Destination.

#### Scenario: Reading list shown

- **WHEN** the guide has books for the Destination
- **THEN** they are listed with title and, where known, author and link

#### Scenario: No books

- **WHEN** the guide has no books
- **THEN** the reading-list section is omitted

### Requirement: Resource links

The system SHALL present, on the destination page, the Destination's resource
links.

#### Scenario: Links shown

- **WHEN** the guide has resource links
- **THEN** they are listed with a label and open the source in a new tab

#### Scenario: No links

- **WHEN** the guide has no links
- **THEN** the links section is omitted

### Requirement: Points of interest on the map

The system SHALL plot the Destination's points of interest on its regional map.

#### Scenario: Points plotted

- **WHEN** the guide has points of interest for the Destination
- **THEN** they appear as markers on the regional map

#### Scenario: No points

- **WHEN** the guide has no points of interest
- **THEN** only the region highlight and destination marker are shown

### Requirement: When to go

The system SHALL present, on the destination page, a monthly climate summary for
the Destination.

#### Scenario: Climate shown

- **WHEN** the guide has a climate summary
- **THEN** a per-month temperature and precipitation view is shown

#### Scenario: No climate

- **WHEN** the guide has no climate summary
- **THEN** the when-to-go section is omitted

### Requirement: Films and series set here

The system SHALL present, on the destination page, films and series whose
narrative location is the Destination.

#### Scenario: Films shown

- **WHEN** the guide has films or series for the Destination
- **THEN** they are listed

#### Scenario: No films

- **WHEN** the guide has no films or series
- **THEN** the films section is omitted

### Requirement: Similar destinations

The system SHALL present, on the destination page, other recommended
Destinations that resemble it by cached embedding similarity.

#### Scenario: Similar destinations shown

- **WHEN** other Destinations resemble the current one
- **THEN** they are listed and link to their pages

#### Scenario: No similar destinations

- **WHEN** no other Destination resembles it
- **THEN** the similar-destinations section is omitted

### Requirement: Suggested itineraries

The system SHALL present, on the destination page, the Destination's itineraries,
marking any AI-generated itinerary as such and showing its sources.

#### Scenario: Curated itinerary shown

- **WHEN** the guide has a curated itinerary
- **THEN** it is listed with its title and a link

#### Scenario: AI itinerary labelled

- **WHEN** the guide has an LLM-synthesised itinerary
- **THEN** it is shown marked as AI-generated with its sources

#### Scenario: No itineraries

- **WHEN** the guide has no itineraries
- **THEN** the itineraries section is omitted
