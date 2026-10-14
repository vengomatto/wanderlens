# Proposal

## Why

Follow-up to `assessment-fixes`: on live data, 3 of 398 marker names still carried
a stray `[[` because their wikitext link was unclosed (`name=[[Sintra`). The
cleaner should be robust to that shape.

## What Changes

- **Robust marker cleaning.** `_clean_title` removes stray link brackets and takes
  the display alias after a `|` regardless of whether the link is well formed, so
  no bracket markup survives into a name or id.
- No **BREAKING** changes.

## Capabilities

### Modified Capabilities
- `destination-catalog`: marker values are cleaned even when the link is
  malformed.

## Impact

- `wanderlens/catalog/wikivoyage.py`; tests.
