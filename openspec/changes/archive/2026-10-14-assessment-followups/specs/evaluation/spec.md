# Spec Delta

## MODIFIED Requirements

### Requirement: Regression gate
The system SHALL provide an evaluation script that prints the metrics and fails
when MRR drops beyond a **relative** margin — a percentage of the stored baseline
— so a near-zero baseline cannot make the gate unfailable.

#### Scenario: Regression fails
- **WHEN** the script runs and MRR falls beyond the relative margin
- **THEN** the script exits non-zero

#### Scenario: Within the margin passes
- **WHEN** MRR is within the relative margin of the baseline
- **THEN** the script exits zero
