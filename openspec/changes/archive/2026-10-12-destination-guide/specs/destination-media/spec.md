# Spec Delta

## MODIFIED Requirements

### Requirement: Fetch free destination media

The system SHALL retrieve, for a Destination, a gallery of at least ten images
where available, an expanded travel-oriented extract, and a link to the source
article, drawing only on free, keyless sources.

#### Scenario: Media retrieved

- **WHEN** media is requested for a Destination with coverage
- **THEN** it gains one or more images, an expanded extract, and a source link

#### Scenario: Gallery of ten

- **WHEN** a Destination has enough imagery in the free sources
- **THEN** its gallery holds at least ten images

#### Scenario: Travel-oriented extract

- **WHEN** a travel guide page exists for the Destination
- **THEN** the expanded extract is sourced from it, with the encyclopedia as fallback

#### Scenario: No media available

- **WHEN** no source returns anything for a Destination
- **THEN** the Destination remains usable without media
