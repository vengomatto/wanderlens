# destination-media Specification

## Purpose
Retrieves and caches a Destination's images, expanded description, source
attribution, and region geometry from free sources, so the web layer can render a
rich destination page entirely from local data.

## Requirements

### Requirement: Fetch free destination media

The system SHALL retrieve, for a Destination, a gallery of at least ten curated
place images where available, an expanded travel-oriented extract, and a link to
the source article, drawing only on free, keyless sources.

#### Scenario: Media retrieved

- **WHEN** media is requested for a Destination with coverage
- **THEN** it gains a curated gallery, an expanded extract, and a source link

#### Scenario: Gallery of ten

- **WHEN** a Destination has enough curated imagery in the free sources
- **THEN** its gallery holds at least ten images

#### Scenario: Travel-oriented extract

- **WHEN** a travel guide page exists for the Destination
- **THEN** the expanded extract is sourced from it, with the encyclopedia as fallback

#### Scenario: No media available

- **WHEN** no source returns anything for a Destination
- **THEN** the Destination remains usable without media

### Requirement: Cache media locally

The system SHALL persist fetched media so it is retrieved at most once and later
renders work without network access.

#### Scenario: Cache avoids refetch

- **WHEN** media already exists for a Destination
- **THEN** no provider request is made for it

#### Scenario: Offline reuse

- **WHEN** the host has no network access and cached media exists
- **THEN** the rich page still renders from the cache

### Requirement: Preserve attribution

The system SHALL record, for each cached image and for the extract, its source
and license or attribution so the origin is shown.

#### Scenario: Attribution recorded

- **WHEN** an image or extract is cached
- **THEN** its source and license/attribution are stored with it

### Requirement: Resolve a region geometry

The system SHALL resolve a region geometry for each Destination — a precise
polygon when one exists, otherwise an approximate area sized to the destination's
granularity — so the destination can be highlighted on a map.

#### Scenario: Precise polygon

- **WHEN** an authoritative boundary for the Destination is available
- **THEN** its polygon is stored as the region geometry

#### Scenario: Approximate fallback

- **WHEN** no boundary is available
- **THEN** an approximate area sized to the Destination's granularity is stored

#### Scenario: No coordinates

- **WHEN** the Destination has no usable coordinates
- **THEN** no region geometry is stored

### Requirement: Region geometry is flagged

The system SHALL mark whether a region geometry is precise or approximate so the
interface can label it.

#### Scenario: Kind recorded

- **WHEN** a region geometry is stored
- **THEN** it records whether it is precise or approximate

### Requirement: Best-effort provider chain

The system SHALL obtain media through an ordered chain of providers, where a
provider that returns nothing or errors MUST NOT fail the run.

#### Scenario: First provider wins

- **WHEN** an earlier provider returns media
- **THEN** later providers are not called for that Destination

#### Scenario: Failure falls through

- **WHEN** a provider errors or returns nothing
- **THEN** the next provider is tried and the run continues

### Requirement: Media is fetched outside the request path

The system SHALL fetch media during recommendation generation, not while serving
web pages, so rendering a page never calls an external service.

#### Scenario: Fetched during recommendations

- **WHEN** recommendations are generated
- **THEN** media for the recommended Destinations is fetched and cached

#### Scenario: Rendering uses cache only

- **WHEN** a destination page is rendered
- **THEN** it reads cached media and makes no external request

### Requirement: Curated image sourcing

The system SHALL source a Destination's images from curated place imagery — the
item's own image, its encyclopedia article's media, and its Commons category —
rather than from a proximity search.

#### Scenario: Curated sources used

- **WHEN** images are gathered for a Destination
- **THEN** they come from its article media, item image, and Commons category

#### Scenario: Item image leads

- **WHEN** the Destination's item has a representative image
- **THEN** that image is used as the hero image

### Requirement: Image quality filtering

The system SHALL exclude unsuitable images — icons, logos, maps, flags, diagrams,
low-resolution files, and unsupported formats — and deduplicate the gallery, so
only usable photographs remain.

#### Scenario: Non-photographic files dropped

- **WHEN** a candidate image is an icon, logo, map, flag, or diagram
- **THEN** it is not included in the gallery

#### Scenario: Low resolution dropped

- **WHEN** a candidate image is narrower than the minimum width
- **THEN** it is not included in the gallery

#### Scenario: Deduplicated

- **WHEN** the same image appears from more than one source
- **THEN** it appears once in the gallery

### Requirement: Proximity gallery as fallback

The system SHALL use the proximity image search only when the curated sources
yield too few images for the Destination.

#### Scenario: Fallback engaged

- **WHEN** curated sources yield fewer than the fallback threshold of images
- **THEN** nearby geotagged images are added to fill the gallery

#### Scenario: Fallback not engaged

- **WHEN** curated sources yield enough images
- **THEN** no proximity search is performed
