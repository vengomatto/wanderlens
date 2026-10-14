# Proposal

## Why

From `docs/IMPROVEMENT_PLAN.md` (B1, B2): the catalog is thin (~20 places per
country), Europe-only, and noisy. Wikivoyage country pages limit "Cities" and
"Other destinations" to nine entries, the parser reads *every* link inside the
"Regions" prose (so Rome is tagged `region`), and lookups re-search by name
because the id carries no stable identity — which also disables the Wikidata
boundary path (`regions.py` only uses P402 for `wd:` ids, but the catalog uses
`wv:`).

## What Changes

- **A stable identity.** A Destination records the Wikidata QID when the page
  exposes one, and media/region lookups prefer it over a name search.
- **A better parser.** Read the section's *list items* and the
  `{{marker}}`, `{{listing}}`, and `{{Regionlist}}` templates (coordinates and
  QIDs come with them), derive granularity from where a link appears, and drop
  links to the parent country or other countries.
- **Global coverage.** The candidate countries become configurable, so the pool
  can extend beyond the hard-coded European set.
- **A quality gate.** Destinations can be filtered to those with coordinates and
  a minimum lead length.
- No **BREAKING** changes; the existing catalog keeps working.

## Capabilities

### Modified Capabilities
- `destination-catalog`: stable QID identity, a section-aware parser with
  templates, configurable coverage, and a quality gate.

## Impact

- `wanderlens/core/models.py`, `catalog/destinations.py`: `Destination.wikidata_id`.
- `wanderlens/catalog/wikivoyage.py`: parser and builder.
- `wanderlens/catalog/regions.py`, `media.py`: prefer the QID.
- `wanderlens/config.py`: catalog countries and quality-gate settings.
- Tests with fixture wikitext (no network).
