# Tasks

## 1. Stable identity

- [x] 1.1 Add `wikidata_id` to `Destination` and its serialization; record it from the Wikivoyage page; verify a test that it is captured and round-trips.
- [x] 1.2 Use the QID for the Wikidata boundary lookup (P402) in `regions.py`; verify a test that a Destination with a QID uses it.

## 2. Parser

- [x] 2.1 Rewrite the Wikivoyage section parser to read list items and marker/listing templates (coordinates and QIDs), derive granularity from the section, and drop the parent/other-country links; verify tests with fixture wikitext.
- [x] 2.2 Build destinations using template coordinates and the page QID; verify a test for both.

## 3. Coverage and gate

- [x] 3.1 Make the candidate countries configurable and add an optional minimum-extract quality gate; verify the gate test and config parse.
- [x] 3.2 Update `README.md` for the parser, QID, coverage, and gate; verify the documented commands run.

## 4. Verification

- [x] 4.1 Run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
