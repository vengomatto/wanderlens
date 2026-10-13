# Spec Delta

## ADDED Requirements

### Requirement: Render the destination case
The web layer SHALL render a Destination's case — its narrative and citation
links — on the destination page, from cached data only, and SHALL omit the
section when no case exists.

#### Scenario: Case shown
- **WHEN** a Destination has a stored case
- **THEN** its narrative and citation links are shown

#### Scenario: No case
- **WHEN** no case is stored
- **THEN** the section is omitted and the page still renders

### Requirement: Render travel diaries and itineraries
The web layer SHALL render a Destination's travel diaries, its itineraries
(including the deterministic one), and its formatted description from cached data
only.

#### Scenario: Itinerary rendered
- **WHEN** a Destination has a stored itinerary
- **THEN** its day-by-day plan is shown, marked with its source

#### Scenario: Diaries rendered
- **WHEN** a Destination has stored diaries
- **THEN** they are shown as labelled links

### Requirement: Offer external photo search links
The web layer SHALL offer outbound links to external photo searches for a
Destination without embedding proprietary images.

#### Scenario: External search offered
- **WHEN** a destination page is rendered
- **THEN** external photo-search links are available and no proprietary image is embedded
