# photo-ingestion Specification

## Purpose
Reads a Photo Archive through a source-agnostic port and exposes per-photo
metadata (capture time, GPS, dimensions) to the rest of Wanderlens.

## Requirements

### Requirement: Read photos from a local folder
The system SHALL discover supported image files in a configured folder and treat
each as a Photo in the archive.

#### Scenario: Ingesting a folder
- **WHEN** the user runs ingestion against a folder containing supported images
- **THEN** the system enumerates each supported image as a Photo

#### Scenario: Unsupported files are skipped
- **WHEN** the folder contains a non-image file
- **THEN** the system ignores it and continues ingesting the images

### Requirement: Extract per-photo metadata
The system SHALL extract capture time, GPS coordinates, and pixel dimensions from
each Photo's metadata, recording missing fields as absent rather than failing.

#### Scenario: Photo with GPS
- **WHEN** an ingested Photo carries GPS metadata
- **THEN** its coordinates and capture time are recorded

#### Scenario: Photo without GPS
- **WHEN** an ingested Photo carries no GPS metadata
- **THEN** it is still ingested with an absent location

### Requirement: Source-agnostic ingestion
The system SHALL ingest through a Photo Source port so a new archive source can
be added without changing photo processing behavior.

#### Scenario: Adding a new source
- **WHEN** a new Photo Source implementation is registered
- **THEN** the system ingests from it without changes to metadata extraction

### Requirement: Idempotent ingestion
The system SHALL not create duplicate Photos when the same folder is ingested
more than once.

#### Scenario: Re-running ingestion
- **WHEN** ingestion is run again over an unchanged folder
- **THEN** no additional Photos are stored
