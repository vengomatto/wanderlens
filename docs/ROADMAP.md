# Roadmap

Deferred decisions, captured for the next phase. Not commitments — a parking lot.

## v2 — Rich recommendations (description + why)

- Every Recommendation must show a **description** of the place **and a "why this
  is a unique match for *you*"** explanation — referencing the specific facets /
  attributes / trips it echoes. The current explanation is a generic template.
- The LLM synthesis seam (`HostedRanker`) is the home for a specific, non-vague
  "why"; the description comes from the catalog provider.
- **Explicit in-app feedback**: let the user rate/favourite Recommendations and
  feed that back into the Taste Profile.

## v2 — Traveler context (questions)

- Capture context a photo archive cannot: **age, language(s), travelling with
  family/friends, ages of children**, season, pace, budget, mobility.
- Elicit via a **short questionnaire per trip-search iteration**, with sensible
  **defaults** from past answers and the profile; persist so it sharpens over
  time. (Supersedes the earlier "trip context" note: you travel with a toddler
  and minimise accommodation changes.)
- Feeds ranking, the explanation, and the **novelty-vs-familiarity** balance.

## v2 — Itinerary design

- Once a Destination is chosen, **smartly design an itinerary** (day-by-day),
  grounded in the user's taste/photos and the traveler context (children ages,
  pace, season, distance between stops).

## Destination granularity (areas, not municipalities)

- **Done:** the recommendation catalog is now built from **Wikivoyage** at area
  granularity (Regions / Cities / Other destinations), e.g. *Epirus*,
  *Algarve*, *Cinque Terre*. GeoNames is retained only for offline
  reverse-geocoding of visited trips (`WANDERLENS_CATALOG_SOURCE`).
- **Remaining:** use the `granularity` tag to filter/boost (favour areas over
  small towns); clean section-link noise (e.g. a page linked under the wrong
  country, "Bosnia and Herzegovina (Croatia)"); and add the
  **famous vs uncommon** signal.

## Strategy — where the value is (catalog vs profiling)

- **The catalog is not the moat.** Wikipedia/Wikivoyage/Wikidata are public and
  ground the app; anyone can query them. The defensible value is the **taste
  profile** (from the user's private photos), the **matching**, and the
  **famous↔uncommon mix calibrated per user**.
- **Recommend both famous and uncommon places.** Famous = high confidence, low
  discovery. Uncommon = the reason to use the app over a search engine.
- **Uncommon needs a broader catalog + a popularity signal.**
  - Broaden with **open data / APIs**, not scraping: OpenStreetMap/Overture
    (everything, tagged), OpenTripMap, Foursquare free tier, Wikidata.
  - Add a **popularity/novelty signal** (e.g. Wikimedia Pageviews; OSM tag
    richness) so `uncommon = low popularity ∧ high taste-match` is measurable.
  - Scraping (Google/TripAdvisor/blogs) is a **last resort**: ToS-grey and
    fragile. Only where open data genuinely lacks coverage.
- **Smart layer for discovery, deterministic layer for truth.** The LLM
  *hypothesizes* uncommon candidates; OSM/Wikidata *validate* existence,
  coordinates, and features. Balance famous vs uncommon from the user's
  **novelty-vs-familiarity** preference.

## v2 — Smart (non-deterministic) layer

- At some point the deterministic core (embeddings + vocabulary attributes) is
  not enough; we want a *bit* of smart, non-deterministic AI in **attribution**
  and/or **recommendations**.
- **Attribution:** LLM extraction with a schema constrained to the shared
  vocabulary, reasoning over a *trip's* photos together (vibe + attributes),
  instead of per-photo comma tags.
- **Recommendations:** the existing `HostedRanker` seam — LLM does last-mile
  ranking/synthesis and the "why", including novelty-vs-familiarity and
  "self-contained destination" judgement.
- **Guardrails:** deterministic core remains the default and fallback; the smart
  layer is optional/injectable; outputs constrained (JSON schema + vocabulary);
  model+prompt pinned and cached for reproducibility; hard filters (eligibility,
  exclusion) stay deterministic; quality measured with the hold-out.

## v2 — Interface

- **Web app** — layered on the same core as the CLI.
- **Chat** — via the existing Telegram/nanobot setup, same core.

## v2 — Incremental ingestion (background)

- **Detect new photos automatically** — watch the archive (filesystem watcher or
  cheap poll) and ingest new/changed files without a manual `ingest`.
- **Run CLIP in the background** — embed new photos in a worker/queue and persist
  incrementally, so the CPU-heavy step never blocks the user.
- **Foreground stays fast** — `recommend` / `profile show` operate on whatever is
  already embedded; a normal run should feel like **10–30 s**, not minutes.
- Implications: a job queue, incremental DB writes, path-change invalidation, and
  a "profile is N photos behind" indicator.

## Cross-cutting — Open-source readiness

- v1 is single-user, but foundations must not assume it stays that way
  (see the multi-user foundation decision in the ADRs / session).

## Providers

- Destination descriptions come from an ordered provider chain. Implemented:
  `wikimedia` (Wikipedia/Wikidata), `openstreetmap` (free OSM features via
  Nominatim + Overpass, best-effort), and `llm` (OpenRouter, no search by
  default). Order is configurable. Next candidates: a curated local file.
- Attribute tags from the VLM are still freeform comma lists; move to structured
  extraction constrained to the shared vocabulary.

## Known limitations

- **Exclusion is by proximity** (default 60 km around each visited trip,
  `WANDERLENS_EXCLUDE_RADIUS_KM`), not by country. Geography is still only used
  to exclude; it is not yet a positive taste signal. The earlier idea of
  two-level country/region **weighting** (country 30 / region 70) is deferred
  until geography proves useful for ranking.
- **Country is a coarse proxy for culture.** What matters is the *vibe* of a
  place (captured today by attributes/embeddings). A future direction is to elicit
  explicit preferences — e.g. whether the user wants to **re-experience the same
  vibes** or seek *novelty* — and to model that orientation alongside the
  photo-derived taste.

- **Ranking blends attribute matching with faceted embeddings.** Taste is now a
  set of per-trip facets (scored by best match, not a global mean) and attribute
  weight is cross-trip recurrence. Coastal destinations still lead; the embedding
  term stays flat because destination text is thin. Next lever: richer destination
  attributes, and `alpha` tuning.
- **Trip splitting** is a fixed 18h / 150km heuristic; the Malta archive split
  into 2 trips over one overnight gap. Make thresholds configurable.
