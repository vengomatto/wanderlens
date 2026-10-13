# Spec Delta

## ADDED Requirements

### Requirement: Deterministic POI-based itinerary
The system SHALL build a day-by-day itinerary from the Destination's own points
of interest when no model is available, so a usable itinerary exists without any
key.

#### Scenario: Itinerary without a key
- **WHEN** a guide is built with no model configured and the Destination has points of interest
- **THEN** a day-by-day itinerary is derived from those points and stored

#### Scenario: No points, no itinerary
- **WHEN** the Destination has no usable points of interest and no model
- **THEN** no synthetic itinerary is stored and the guide remains usable

### Requirement: Travel diaries and journals
The system SHALL present a deduplicated set of travel diaries, journals, and
first-person guides for the Destination, drawn from the travel guide's links and
a configurable blog list, each with a label and URL.

#### Scenario: Diaries listed
- **WHEN** travel diaries or journals are found for a Destination
- **THEN** they are listed with a label and a URL

#### Scenario: No diaries
- **WHEN** none are found
- **THEN** the diaries section is omitted

### Requirement: Structured destination description
The system SHALL render a Destination's description as a scannable structure — a
lead sentence followed by highlights — rather than a single wall of extract, and
SHALL enrich it with the hosted model when available.

#### Scenario: Structured prose
- **WHEN** a Destination description is rendered
- **THEN** it presents a lead sentence and separate highlights

#### Scenario: Enriched when possible
- **WHEN** a hosted model is configured
- **THEN** the description is enriched while the keyless structure remains the fallback
