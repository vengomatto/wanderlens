# image-matching Specification

## Purpose

Builds a visual vector for each candidate Destination from its own images, so a
photo can be matched against a place image-to-image rather than across modalities.

## Requirements

### Requirement: Destination image embeddings
The system SHALL derive, for a Destination with images, a visual vector from a
few of its hero images, using the local image embedder, and cache it.

#### Scenario: Vector derived
- **WHEN** a Destination has usable images
- **THEN** a visual vector is derived from them and cached

#### Scenario: Cached once
- **WHEN** a Destination already has a visual vector
- **THEN** it is reused rather than recomputed

#### Scenario: No images
- **WHEN** a Destination has no usable images
- **THEN** no visual vector is stored and the run continues

### Requirement: Opt-in and non-fatal
The system SHALL enable image matching only when explicitly requested, and MUST
NOT fail the run when images cannot be fetched or embedded.

#### Scenario: Off by default
- **WHEN** image matching is not requested
- **THEN** ranking is unchanged

#### Scenario: Failure tolerated
- **WHEN** fetching or embedding a Destination's images fails
- **THEN** the run continues and that Destination falls back to text
