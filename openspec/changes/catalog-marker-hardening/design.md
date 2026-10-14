# Design

## Context

See `proposal.md`. `_clean_title` parsed a well-formed `[[target|alias]]`; a
malformed link left stray brackets. Live data showed 3 such names.

## Decisions

- `_clean_title` removes all `[[`/`]]`, takes the display part after a `|`, and
  drops a `#fragment` — robust to well-formed and malformed links alike.

## Risks / Trade-offs

- **A literal `|` in a plain name** → only affects bracket-sourced values, which
  are links by construction; acceptable.
