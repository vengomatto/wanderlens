# synthetic-archive Specification

## Purpose

Generates a deterministic mock photo archive and candidate catalog on disk so the
full taste-and-recommendation pipeline can be run and evaluated on a broad dataset
without the owner's photos.

## Requirements

### Requirement: Generate a runnable synthetic archive
The system SHALL generate, into a target directory, a mock photo archive (trips
with capture times, coordinates, and attributes) and a matching candidate catalog
of Destinations, so `ingest → profile → recommend` can be run end-to-end.

#### Scenario: Archive materialised
- **WHEN** the synthetic archive is generated for a target directory
- **THEN** it writes photos, their metadata, and a candidate catalog that the normal pipeline can read

#### Scenario: Broad dataset
- **WHEN** the archive is generated
- **THEN** it contains many trips and many candidate Destinations, not a handful

### Requirement: Synthetic archive is deterministic
The system SHALL produce the same archive for the same parameters, so runs are
reproducible.

#### Scenario: Repeated generation
- **WHEN** the archive is generated twice with the same parameters
- **THEN** the files and their contents are identical

### Requirement: Synthetic archive exercises the taste logic
The generated archive SHALL include trips whose attributes imply a known taste
and Destinations that do and do not match it, so ranking can be judged against
known expectations.

#### Scenario: Known relevant destinations
- **WHEN** recommendations run over the synthetic archive
- **THEN** Destination matching the archive's taste are expected among the top results
