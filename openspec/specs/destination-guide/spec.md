# destination-guide Specification

## Purpose
Gathers and caches a Destination's travel-guide content — rich prose, links,
books, points of interest, climate, films, and itineraries — from free sources
plus an optional cached LLM itinerary, so the web layer can present a
trip-preparation page offline.

## Requirements

### Requirement: Gather travel-guide content

The system SHALL gather, for a Destination, a rich travel description, resource
links, a reading list, points of interest, climate, films, and itineraries from
free sources, without scraping.

#### Scenario: Guide gathered

- **WHEN** a guide is built for a Destination with coverage
- **THEN** it carries a rich description and any available links, books, points of interest, climate, films, and itineraries

#### Scenario: Partial coverage

- **WHEN** some sections have no source
- **THEN** the guide is stored with the sections it does have and remains usable

### Requirement: Cache the guide locally

The system SHALL persist a Destination's guide so it is built at most once and
later renders work without network access.

#### Scenario: Cache avoids rebuild

- **WHEN** a guide already exists for a Destination
- **THEN** no source request is made for it

#### Scenario: Offline reuse

- **WHEN** the host has no network access and a cached guide exists
- **THEN** the guide section still renders from the cache

### Requirement: Rich travel description

The system SHALL source the expanded description from a travel guide
(Wikivoyage) so the prose is travel-oriented, using the encyclopedia only as a
fallback.

#### Scenario: Travel guide prose

- **WHEN** a travel guide page exists for the Destination
- **THEN** the rich description comes from it

#### Scenario: Encyclopedia fallback

- **WHEN** no travel guide page exists
- **THEN** the encyclopedia extract is used instead

### Requirement: Reading list

The system SHALL list novels and books set in or about the Destination, derived
from work-to-place links and an open library search.

#### Scenario: Books found

- **WHEN** books are associated with the Destination
- **THEN** they are listed with a title and, where known, an author and a link

#### Scenario: No books

- **WHEN** no books are found
- **THEN** the reading-list section is omitted

### Requirement: Resource links

The system SHALL present a deduplicated set of resource links for the
Destination, including its official site, travel guide, encyclopedia page, media
category, and map.

#### Scenario: Links aggregated

- **WHEN** links are gathered for a Destination
- **THEN** duplicates are removed and each link carries a label and a URL

#### Scenario: No links

- **WHEN** no links are found
- **THEN** the links section is omitted

### Requirement: Points of interest

The system SHALL extract points of interest (notable *see* and *do* places) from
the travel guide, with coordinates where available, for display on a map.

#### Scenario: Points with coordinates

- **WHEN** the travel guide lists places with coordinates
- **THEN** they are stored as points of interest with their position

#### Scenario: No points

- **WHEN** the travel guide lists no usable points
- **THEN** no points of interest are stored

### Requirement: When to go

The system SHALL derive a monthly climate summary for the Destination from free
historical weather data, so the user can judge the best months to visit.

#### Scenario: Climate summarised

- **WHEN** climate is derived for a Destination with coordinates
- **THEN** a per-month temperature and precipitation summary is stored

#### Scenario: No coordinates

- **WHEN** the Destination has no coordinates
- **THEN** no climate summary is stored

### Requirement: Films and series set here

The system SHALL list films and series whose narrative location is the
Destination.

#### Scenario: Films found

- **WHEN** works are linked to the Destination as their narrative location
- **THEN** the films and series are listed

#### Scenario: No films

- **WHEN** no such works are found
- **THEN** the films section is omitted

### Requirement: Curated itineraries

The system SHALL include itineraries curated by the travel guide for the
Destination or its region.

#### Scenario: Curated itinerary listed

- **WHEN** the travel guide provides a curated itinerary
- **THEN** it is listed with its title and a link

### Requirement: Optional LLM itinerary

The system SHALL optionally synthesise a day-by-day itinerary using a search-
grounded LLM, constrained to structured output, cached, marked as AI-generated,
and citing its sources; a failure MUST NOT fail the run.

#### Scenario: Itinerary synthesised

- **WHEN** LLM synthesis is enabled and succeeds
- **THEN** a day-by-day itinerary is stored, marked as AI-generated and with its sources

#### Scenario: Synthesis disabled or failed

- **WHEN** LLM synthesis is disabled, unavailable, or errors
- **THEN** the guide is stored without a synthetic itinerary and the run continues

#### Scenario: Reproducible

- **WHEN** an itinerary has already been synthesised for a Destination
- **THEN** it is reused from cache rather than synthesised again

### Requirement: Guide is built outside the request path

The system SHALL build guides through a dedicated command, not while serving web
pages, so rendering a page never calls an external service.

#### Scenario: Built by the guide command

- **WHEN** the guide command runs
- **THEN** guides for the recommended Destinations are built and cached

#### Scenario: Rendering uses cache only

- **WHEN** a destination page is rendered
- **THEN** it reads the cached guide and makes no external request

### Requirement: Deterministic POI-based itinerary
The system SHALL build a day-by-day itinerary from the Destination's own points
of interest when no model is available, grouping the points into days **by
geographic proximity** so a day stays in one area, falling back to a simple split
when coordinates are missing.

#### Scenario: Itinerary without a key
- **WHEN** a guide is built with no model configured and the Destination has points of interest
- **THEN** a day-by-day itinerary is derived from those points and stored

#### Scenario: Points grouped by area
- **WHEN** the points of interest form distinct nearby clusters
- **THEN** each day's points come from the same cluster

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

### Requirement: Best months and climate match
The system SHALL compute, for a Destination, its best months relative to the
user's climate preference and a climate-match score, cached, and MUST NOT fail
the run when climate data is unavailable.

#### Scenario: Best months computed
- **WHEN** a Destination has monthly climate and the user has a climate preference
- **THEN** its best months and a climate-match score are computed and cached

#### Scenario: No preference
- **WHEN** the user has no climate preference
- **THEN** no best months or climate match are produced for the Destination

#### Scenario: Failure tolerated
- **WHEN** climate data is unavailable for a Destination
- **THEN** it is stored without best months and the run continues
