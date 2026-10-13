# destination-case Specification

## Purpose

Builds a strong, sourced case for a recommended Destination — a compelling
narrative plus citation links — from free sources, optionally enriched by web
search and a hosted model, so a new place can be argued for rather than listed.

## Requirements

### Requirement: Assemble a sourced case
The system SHALL assemble, for a Destination, a compelling narrative and a set of
citation links drawing on free, keyless sources (travel guide, encyclopedia,
item data, media).

#### Scenario: Case assembled
- **WHEN** a case is built for a Destination with coverage
- **THEN** it carries a narrative and citation links to its sources

#### Scenario: Partial coverage
- **WHEN** some sources are missing
- **THEN** the case is built from those available and remains usable

### Requirement: Optional web-search and LLM enrichment
The system SHALL optionally enrich the case with a web search and a hosted model
that writes a captivating description grounded only in the gathered facts, and
MUST NOT invent places or require a key to work.

#### Scenario: Enriched with a model
- **WHEN** web search and a model are configured and succeed
- **THEN** the case narrative is the model's grounded prose and its sources are cited

#### Scenario: Keyless fallback
- **WHEN** no search or model is configured, or either errors
- **THEN** the case uses the deterministic keyless narrative and the run continues

### Requirement: Case is cached and reproducible
The system SHALL cache a Destination's case by input, model, and prompt version,
so repeat runs reuse it rather than calling the network or model again.

#### Scenario: Reproducible reuse
- **WHEN** a case was already built for the same input, model, and prompt version
- **THEN** the cached case is reused

### Requirement: Case never fails the run
The system SHALL treat case building as best-effort; a missing source, a failed
search, or a model error MUST NOT fail recommendation generation.

#### Scenario: Source failure
- **WHEN** a case source errors
- **THEN** the case omits that part and the recommendation run continues
