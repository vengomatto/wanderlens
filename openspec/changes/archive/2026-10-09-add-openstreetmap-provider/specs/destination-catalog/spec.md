# Spec Delta

## ADDED Requirements

### Requirement: OpenStreetMap feature provider
The system SHALL be able to derive a Destination's descriptive attributes from
OpenStreetMap tags, using a free, keyless OSM service.

#### Scenario: Features resolved
- **WHEN** a place resolves in OpenStreetMap with tags such as coastline, beach,
  harbour, or historic
- **THEN** the Destination gains descriptive feature text naming those attributes

#### Scenario: Place not found
- **WHEN** OpenStreetMap has no match for the place
- **THEN** the provider returns nothing and the chain continues

#### Scenario: No API key or fee
- **WHEN** the OpenStreetMap provider is used
- **THEN** it requires no API key and incurs no per-request search fee
