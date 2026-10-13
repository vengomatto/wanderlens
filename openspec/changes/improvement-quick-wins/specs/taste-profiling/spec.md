# Spec Delta

## ADDED Requirements

### Requirement: Unreadable photos do not abort profiling
The system SHALL skip a photo it cannot read and count it, so one unreadable file
does not fail the whole profiling run.

#### Scenario: Unreadable photo skipped
- **WHEN** a photo cannot be read or decoded
- **THEN** it is skipped, counted, and the run continues

#### Scenario: Count reported
- **WHEN** profiling finishes
- **THEN** the number of skipped photos is available
