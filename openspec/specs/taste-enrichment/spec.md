# taste-enrichment Specification

## Purpose

Turns a sparse, flat set of photo tags into a richer, structured taste and
destination representation using a hosted cheap model, invoked as part of the
chain with a deterministic local fallback.

## Requirements

### Requirement: Structured per-trip attributes
The system SHALL derive, for each trip, a structured set of canonical attributes
(subjects and activities) rather than only free-text tags, and SHALL record them
against that trip.

#### Scenario: Trip attributed structurally
- **WHEN** a trip is enriched
- **THEN** it gains a structured set of canonical attributes describing its subjects and activities

#### Scenario: Sparse tags still attributed
- **WHEN** a trip's raw tags are thin or empty
- **THEN** the system derives attributes from the trip's photos without failing

### Requirement: Richer destination representation
The system SHALL build each Destination's embedding input from its structured
attributes and descriptive text when available, so the embedding input is richer
than name and country alone.

#### Scenario: Enriched destination text
- **WHEN** a Destination has structured attributes
- **THEN** its embedding text includes those attributes in addition to its description

### Requirement: Hosted enrichment is injectable and cached
The system SHALL perform enrichment through an injectable hosted-model seam,
cached per input, model, and prompt version, so repeated runs reuse prior output
without recomputation.

#### Scenario: Reproducible reuse
- **WHEN** the same input, model, and prompt version were enriched before
- **THEN** the cached result is reused instead of calling the model again

### Requirement: Deterministic fallback, never fatal
The system SHALL fall back to its local, deterministic representation when the
enrichment model is unavailable or errors, and MUST NOT fail the run.

#### Scenario: Model unavailable
- **WHEN** no enrichment model is configured or reachable
- **THEN** the profile and destination representations fall back to the local deterministic form

#### Scenario: Model error
- **WHEN** the enrichment model errors for an input
- **THEN** that input uses the deterministic fallback and the run continues

### Requirement: Enrichment preserves privacy boundary
The system SHALL send only sampled Photos or derived text to the hosted model,
never the full archive, consistent with local embedding computation.

#### Scenario: Only samples sent
- **WHEN** enrichment runs
- **THEN** only sampled Photos or already-derived text leave the host
