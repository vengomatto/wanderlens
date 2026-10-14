# Spec Delta

## ADDED Requirements

### Requirement: Clean marker values
The system SHALL strip wiki markup from a parsed marker/listing `name` (link
brackets, an optional display alias, and any `#fragment`) before it becomes a
title, id, or lookup key, so names and ids are clean.

#### Scenario: Bracketed name cleaned
- **WHEN** a marker's name is given as `[[Rome]]` or `[[Rome|Roma]]`
- **THEN** the resulting title is `Rome` or `Roma` respectively

### Requirement: Quality gate logs drops
The system SHALL, when the catalog quality gate is enabled, drop entries without
coordinates or a long-enough lead and SHALL record what it dropped.

#### Scenario: Gate records drops
- **WHEN** the gate is enabled and an entry lacks coordinates
- **THEN** the entry is dropped and the reason is recorded
