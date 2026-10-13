# Spec Delta

## ADDED Requirements

### Requirement: Optional climate preference
The system SHALL accept an optional climate weight and season preference that
bias ranking toward Destinations whose climate matches the user's preference;
with both unset, ranking MUST be unchanged.

#### Scenario: Climate bias applied
- **WHEN** a positive climate weight is set and Destinations have a climate match
- **THEN** higher-matching Destinations rank above otherwise-equal lower-matching ones

#### Scenario: Season preference
- **WHEN** a season preference is set
- **THEN** Destinations whose best months include that season are preferred

#### Scenario: Off by default
- **WHEN** no climate weight or season is set
- **THEN** the ranking matches the climate-free ranking
