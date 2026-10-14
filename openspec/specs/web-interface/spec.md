# web-interface Specification

## Purpose
A local, read-only web presentation of the Taste Profile, visited Trips, and
Recommendations, reusing the existing core read paths so the app's value is
visible without the CLI.

## Requirements

### Requirement: Local dashboard over persisted data

The system SHALL serve a read-only web dashboard bound to localhost for a single
user, presenting data the CLI has already persisted, without recomputing or
mutating stored state.

#### Scenario: Launching the dashboard

- **WHEN** the user launches the dashboard
- **THEN** it serves pages on localhost for the configured user

#### Scenario: Existing data shown

- **WHEN** the dashboard is opened after an ingest and a recommend run
- **THEN** it presents the persisted Taste Profile and Recommendations

#### Scenario: No recomputation on view

- **WHEN** a dashboard page is requested
- **THEN** no photo ingestion, tagging, or ranking run is triggered

### Requirement: View the Taste Profile

The system SHALL present the Taste Profile as trips, visited-geography weights,
subject/activity weights, and aesthetic coverage.

#### Scenario: Profile summary

- **WHEN** the user opens the profile view
- **THEN** trips, visited geography, subject weights, and the embedded-photo count are shown

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

### Requirement: Visit evidence from the Photo Archive

The system SHALL present, for a visited Trip, the user's own Photos and the
trip's attributes as the evidence behind the taste.

#### Scenario: Trip detail

- **WHEN** the user opens a trip
- **THEN** its Photos are shown as thumbnails alongside its attributes and location

### Requirement: Map visited and recommended places

The system SHALL plot visited Trips and recommended Destinations on a map using
keyless map tiles.

#### Scenario: Places plotted

- **WHEN** the map view is shown
- **THEN** visited trips and recommended destinations appear as markers

### Requirement: Graceful empty states

The system SHALL show a guiding empty state, rather than an error, when the
profile or the recommendations have not been generated yet.

#### Scenario: No profile yet

- **WHEN** the dashboard is opened before any ingestion
- **THEN** it explains how to generate the profile

#### Scenario: No recommendations yet

- **WHEN** the recommendations have not been generated
- **THEN** it explains how to generate them

### Requirement: Render without the model runtime

The system SHALL render the dashboard from persisted data only, without loading
the embedding or vision model runtime.

#### Scenario: Dashboard without models

- **WHEN** any dashboard page is rendered
- **THEN** no embedding or vision model is loaded

### Requirement: Local-only presentation

The system SHALL serve the dashboard and the user's Photos locally and MUST NOT
transmit Photos or profile data to any external service.

#### Scenario: No external calls

- **WHEN** any dashboard page is rendered
- **THEN** no Photo or profile data is sent to an external service

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

### Requirement: Show the evidence behind the match

The system SHALL present, on the destination page, the evidence behind the match
— the closest visited Trip and the shared attributes — in addition to the
explanation.

#### Scenario: Evidence shown

- **WHEN** a destination page has stored match evidence
- **THEN** it shows the closest visited trip and the shared attributes as chips

#### Scenario: No evidence

- **WHEN** a destination page has no match evidence
- **THEN** it shows the explanation alone

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

### Requirement: Famous or uncommon label

The system SHALL show, on the recommendation card and the destination page, a
label indicating whether the Destination is famous, balanced, or uncommon.

#### Scenario: Label shown

- **WHEN** a Recommendation has a popularity score
- **THEN** its card and destination page show a famous, balanced, or uncommon label

#### Scenario: No popularity

- **WHEN** a Recommendation has no popularity score
- **THEN** no label is shown

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

### Requirement: Show climate fit
The web layer SHALL show, on the destination page, the Destination's best months
and climate-match score when available, from cached data only.

#### Scenario: Climate fit shown
- **WHEN** a Destination has best months or a climate match stored
- **THEN** the destination page shows them

#### Scenario: No climate fit
- **WHEN** no best months or climate match are stored
- **THEN** the section is omitted and the page still renders

### Requirement: Show the destination profile
The web layer SHALL show a Destination's structured profile — vibe chips and
suitability fields, with model-estimated fields marked — on the destination page,
from cached data only.

#### Scenario: Profile shown
- **WHEN** a Destination has a stored profile
- **THEN** its vibe chips and suitability fields are shown, with estimated fields labelled

#### Scenario: No profile
- **WHEN** no profile is stored
- **THEN** the section is omitted and the page still renders

### Requirement: Feedback is a POST that stays put
The web layer SHALL record feedback through a POST request that returns the
refreshed feedback control in place, rather than a GET that writes state and
reloads the page.

#### Scenario: Posting feedback
- **WHEN** the user activates a feedback button
- **THEN** the action is recorded and only the feedback control is refreshed

#### Scenario: No JavaScript
- **WHEN** the request is not an HTMX request
- **THEN** the action is recorded and the page redirects back to the destination

### Requirement: Mobile layout does not overflow
The web layer SHALL render without horizontal overflow at narrow viewports, with
a wrapping navigation and a single-column destination grid.

#### Scenario: Narrow viewport
- **WHEN** the page is rendered at a phone width
- **THEN** it does not scroll horizontally and the navigation wraps

### Requirement: Favicon and boosted navigation
The web layer SHALL provide a favicon and SHALL navigate in-app links without a
full page reload where supported.

#### Scenario: No favicon 404
- **WHEN** the page is loaded
- **THEN** a favicon is available and no favicon request 404s

#### Scenario: Boosted links
- **WHEN** an in-app link is followed
- **THEN** it is handled without a full page reload
