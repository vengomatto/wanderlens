# Spec Delta

## ADDED Requirements

### Requirement: Search-grounded itinerary
The system SHALL, when a search provider is configured, ground the LLM itinerary
in web-search results so its suggestions are not invented.

#### Scenario: Grounded itinerary
- **WHEN** an itinerary is synthesised with a search provider configured
- **THEN** the synthesised days are based on the gathered search results

#### Scenario: Ungrounded fallback
- **WHEN** no search provider is configured or search fails
- **THEN** the itinerary is still produced from the points of interest

### Requirement: Default diary sources
The system SHALL include a non-empty default set of travel-diary/journal sources,
in addition to any configured blog list.

#### Scenario: Default diaries present
- **WHEN** a guide is built with no custom blog list
- **THEN** it still offers travel-diary/journal links
