# Design

## Context

See proposal.md — Why. The provider port exists; we need a free provider that
yields attribute-bearing text.

## Goals / Non-Goals

**Goals:**
- A keyless, free provider producing canonical feature words from OSM.
- Default chain `wikimedia → openstreetmap → llm`.
- Respect OSM fair-use.

**Non-Goals:**
- Area/POI density queries (that is Overpass's job) — Nominatim search is enough.
- Replacing Wikimedia; this is additive.

## Decisions

**Nominatim over raw Overpass.** Overpass is powerful but heavier and easier to
over-use; Nominatim's `/search` with `extratags=1` resolves `"<name>, <country>"`
and returns the OSM element's tags (natural, leisure, historic, harbour, class
/type) in one free request. Same OSM data, simpler and fair-use friendly.
*Alternatives:* Overpass area queries (rejected for now: heavier, fuzzier name
matching); paid search (rejected: cost).

**Tags → canonical words.** Map OSM `class`/`type`/`extratags` into the shared
vocabulary ('coastline'→coastal, 'beach'→beach, 'marina'→boats, 'castle'→history,
'town'→city). The resulting phrase is stored as the Destination description, so
ranking's `destination_attribute_set` picks it up unchanged.

**Fair-use.** A descriptive `User-Agent` and a ~1 request/second delay; empty
results return `None` so the chain proceeds.

## Risks / Trade-offs

- **Tag coverage varies by region** → missing tags just yield no description; the
  chain continues to the next provider.
- **Name ambiguity** → country-qualified query plus top result; a wrong match
  degrades one candidate only.
- **Nominatim rate limits** → 1 req/s delay; results cached, so each place is
  queried once.
