# Wanderlens improvement plan

Plan only. No code was changed to produce it. Date: 2026-10-13. Repo state reviewed: `208ce58` (master).

---

## 0. How to read this

You asked for a plan covering design, recommendation logic, navigation, cost optimisation, better sources, and the roadmap. This plan is built from three kinds of evidence. Each finding carries a tag so you know how much to trust it.

| Tag | Meaning |
|---|---|
| **[Verified]** | I ran it (real CLIP model, real Wikivoyage/Wikipedia APIs, the dashboard in a browser) and measured the result |
| **[Code]** | Read directly in the source, not executed. File and line are given |
| **[Hypothesis]** | Reasoned from the code or from general knowledge. Needs a spike before you commit to it |

**Assumptions**

- **"Cost optimisation"** means the running cost of the pipeline (LLM, vision, API calls, compute, bandwidth). Trip budget for the traveller is a separate feature and appears in section 3 and 7.
- **Stack constraint kept:** FastAPI + Jinja + HTMX + Alpine, no JavaScript build step. The plan does not require a rewrite in React or similar.
- **Ground rules kept:** ports and adapters, deterministic ranking by default, hosted model steps cached and never fatal (see `AGENTS.md`).

**Method (what I actually did)**

1. Read the README, ROADMAP, ADRs, all specs, and all source files under `wanderlens/`.
2. Ran the test suite (256 passed, 1 skipped) and `eval --synthetic` in a scratch copy outside the repo.
3. Generated the synthetic archive, ran `recommend` and `guide`, served the dashboard, took screenshots (desktop, mobile, light, dark), and measured payloads.
4. Ran the real CLIP text model on real catalog text, and the repo's own Wikivoyage and pageview code on 7 countries.

Note: the synthetic embedder makes `emb` equal 1.000 for every card, so the screenshots say nothing about taste quality. They are valid for design and navigation only.

---

## 1. Summary

### 1.1 The one-paragraph diagnosis

The weak recommendations are mostly **not** a tuning problem. Three defects feed the ranker bad data before any weight is applied: a text-encoding bug that makes 14% of destinations identical to the embedder, a catalog of about 20 mostly-regional places per country that only covers Europe, and a popularity label that calls almost everything "famous". Fix those first. Adding an LLM re-ranker on top of them would hide the problem and cost money.

The design looks flat for a structural reason: every page is the same beige card, the destination page is 13 identical cards stacked (4164 px tall), and photos (your product's differentiator) are small. A new colour palette will not fix that. A new page structure will.

### 1.2 Top findings

| # | Finding | Tag | Impact |
|---|---|---|---|
| L1 | CLIP text encoder truncates at 77 tokens and drops the end token. Any longer text collapses to one constant vector (cosine 0.9999 between Hvar, Zermatt, Kyoto). 19 of 140 real catalog texts (14%) are affected | **[Verified]** | High |
| L2 | Catalog is Europe-only (30 hard-coded countries) and thin: Croatia 15, Greece 30, Portugal 20, Italy 33, Spain 30, Malta 4. Italy has 0 "city" entries | **[Verified]** | High |
| L3 | Famous/uncommon label: 15 of 17 real destinations are "famous" (Cres, a small island, scores 0.74). The `--novelty uncommon` option is close to inert | **[Verified]** | High |
| L4 | Text-to-image CLIP similarity is compressed, so the embedding term barely discriminates. Different destinations score 0.84 to 0.92 against each other in text space | **[Verified]** | High |
| C1 | `--tag` uploads raw original photo files (full size, with EXIF GPS) to a third party, labelled `image/jpeg` | **[Code]** `models/vision.py:32` | High (cost, privacy) |
| C2 | New trips are never tagged unless you run `--retag`, which re-sends every photo | **[Code]** `pipeline/profile.py:195` | Medium |
| C3 | Cases are built for the 20-item shortlist, then only 5 are shown | **[Code]** `pipeline/recommend.py:313` | Medium |
| D1 | Destination page: 13 identical cards, 1.59 MB, 27 requests. Recommendations page: 2.69 MB, images are 1280 px originals shown in 200 px slots | **[Verified]** | High |
| D2 | Mobile (390 px): page overflows sideways, nav clipped, hero chips collide with the gauge | **[Verified]** | High |
| N1 | Feedback is a GET link that writes state, reloads the page, resets scroll, adds a history entry, and has no CSS (renders as plain text) | **[Verified]** | High |
| N2 | No saved or liked list, no prev/next between destinations, no way to run `ingest` or `recommend` from the UI | **[Code]** | High |
| B1 | Raw wikitext headings (`== Cities == 1 Antofagasta ...`) shown in the "About" card | **[Verified]** | Medium |

---

## 2. Verified defects in detail

### 2.1 L1: CLIP text truncation

**Why it matters.** The embedding score is `alpha * similarity`, and the same vectors drive diversity (MMR) and "similar destinations". A constant vector breaks all three.

**Cause.** `models/embeddings.py:111` does `self._tokenizer.encode(text).ids[:77]`. The tokenizer adds a start and an end token. When the text is longer than 77 tokens, the cut removes the end token. CLIP pools the text at the position of the highest token id (the end token). Without it, the pooled position is the start token, which is identical for every text.

**Evidence.**

| Check | Result |
|---|---|
| Three texts of 82 to 87 tokens (Hvar, Zermatt, Kyoto) | Pairwise cosine 0.9999 |
| One 79-token text vs the same text correctly cut | Cosine 0.75 |
| Real catalog, 140 destinations from 7 countries | 19 texts (14%) over 77 tokens. Median 64.5, p90 82, max 108 tokens |

Note: `destination_text()` appends attributes to the description, and the LLM enrichment path can lengthen it, so the real rate in a full run is likely higher than 14%.

**Fix (small, safe).**

1. Cut to 76 tokens and re-append the end token, or let the tokenizer truncate with its post-processor.
2. Bump the destination embedding cache key (the table key is `(destination_id, model)`, so add a version suffix to `model`) so old collapsed vectors are recomputed.
3. Add a regression test: two different texts over 77 tokens must not have cosine above 0.99.

### 2.2 L2: catalog size, coverage, and noise

**Why Italy has no cities.** Wikivoyage country pages limit "Cities" and "Other destinations" to nine entries by policy. The code reads only those three sections. It also reads every `[[link]]` inside the "Regions" text, including the descriptions, so cities mentioned there (Rome, Turin) are tagged `region` because the first section wins. Result: 30 "region" and 0 "city" for Italy.

**Other measured problems.**

- Croatia's list contains "Hungary" and "Bosnia and Herzegovina" (link noise, already in the ROADMAP).
- Descriptions are cut at exactly 300 characters, mid-sentence (median is 300).
- Some entries are useless for matching: "Eastern Spain is in Spain."
- 30 countries are hard-coded in `DEFAULT_CANDIDATE_COUNTRIES`, all European. If your taste is beach and warm water, Southeast Asia, the Caribbean, and the Indian Ocean can never appear.
- Total pool is roughly 600 places. A typical top-5 is drawn from a very small and very regional list.

### 2.3 L3: popularity label

`normalize_popularity` is `log10(views_12m + 1) / 6`, and "famous" starts at 0.66, which is about 9,000 views per year. Almost every Wikipedia page for a region passes that.

| Destination | Views (12 m) | Score | Label |
|---|---|---|---|
| Dolomites | 610,887 | 0.96 | famous |
| Hvar | 73,449 | 0.81 | famous |
| Cres | 25,866 | 0.74 | famous |
| Magnesia | 9,336 | 0.66 | famous |
| Kvarner | 2,946 | 0.58 | balanced |
| Eastern Spain (page does not exist) | 14 | 0.20 | uncommon |

Two more problems: pageviews are fetched by `destination.name`, not by the exact article, so ambiguous names ("Arcadia", "Magnesia") hit the wrong page. And English Wikipedia views reflect English-speaking interest, not global fame.

### 2.4 Logic problems read from the code

| ID | Problem | Where | Tag |
|---|---|---|---|
| L5 | Two-pass ranking. The first pass (top 20) ignores novelty, diversity, climate, and season. `--season winter` can only reorder those 20, never promote a ski place ranked 40th | `pipeline/recommend.py:277` | **[Code]** |
| L6 | Score mixes incompatible scales: embedding about 0.1 to 0.3, attribute sum can exceed 1, novelty plus or minus 0.075, feedback plus or minus 0.15. Weights are guesses | `core/recommend.py:252` | **[Code]** |
| L7 | Attribute vocabulary is 28 words. Photo conditions ("sunny", "mist", "rain") are in the same vocabulary as places, so a destination text saying "rain" matches your sunny photos | `core/vocabulary.py:50` | **[Code]** |
| L8 | Taste weight = share of trips containing an attribute. Each trip's attributes come from only 3 sampled photos. No signal for how much you loved a trip (photo count, days, recency) | `pipeline/profile.py:147` | **[Code]** |
| L9 | Missing attributes are never penalised, only matched ones are rewarded. A city break scores 0 on "city" for a mountain person, but never negative | `core/recommend.py:248` | **[Code]** |
| L10 | MMR diversity uses the same text vectors. With L1, collapsed destinations look like duplicates of each other and only one survives, at random | `core/recommend.py:153` | **[Code]** |
| L11 | Enrichment, wikivoyage, media, popularity all re-search by name. Synthetic run matched "Coastal Place 16" to a Chilean region and others to "Synthetic cannabinoids". Real ambiguous names will do the same | `catalog/fetch.py`, `catalog/media.py` | **[Verified]** |
| L12 | `recommendations` table is wiped on every run (`run_id` always 1). No history, no "what changed", no way to measure drift | `pipeline/recommend.py:356` | **[Code]** |
| L13 | The explanation shows "closest to your trip 0 trip (similarity 1.00)" and exposes raw cosine values | `core/recommend.py:331` | **[Verified]** |
| L14 | The only quality metric is `eval --synthetic` on 8 destinations with one-hot vectors. It reports precision 1.00 and MRR 1.00, so it cannot show an improvement. The real `eval` holds out one trip and asks if anything within 60 km is in the top 50 | `core/gallery.py` | **[Verified]** |
| L15 | A single unreadable photo (for example HEIC, which is in `SUPPORTED_EXTENSIONS` but has no decoder in the dependencies) aborts the whole profile run, because `_embed_photos` has no error handling | `pipeline/profile.py:99` | **[Hypothesis]** (not triggered, reasoned from code) |
| L16 | Every `ingest` hashes every file in the archive before checking if it is known. Cost grows with archive size | `sources/folder.py:80` | **[Code]** |

---

## 3. Workstream A: recommendation logic

**Goal.** Recommendations a person would call good for them, measurably better than today, and explainable in plain words.

**Principle.** Measure first (A0), then fix data (A1, A2), then change the model (A3 onward). Each step is accepted only if the A0 metrics improve.

### A0. Evaluation harness (do this first)

**Why first.** Today you cannot tell whether a change helped (L14). Every later step depends on this.

| Part | What to build |
|---|---|
| **Leave-one-trip-out over all trips** | For each trip with a location: hide it, build taste from the rest, rank the catalog, record the rank of the first destination within the exclusion radius. Report MRR, Recall@10, Recall@50 averaged over trips. Not a single trip, not pass/fail |
| **Real-photo persona fixtures** | 6 to 8 personas, each 30 to 60 openly licensed Commons photos of known places (alpine, Mediterranean coast, old town, desert, tropical, nordic). Replaces solid-colour synthetic images so CLIP is exercised end to end. Store the file list, not the files |
| **Score diagnostics** | Per run: standard deviation of each component across the catalog, share of destinations with collapsed vectors, and top-20 attribute and country mix. Print it from `recommend --diagnose` |
| **Triage labels** | The swipe mode in section 6 (E3) produces labelled data from you. Use it as a small private test set |
| **Regression gate** | `scripts/eval.sh` prints the metrics and fails if MRR drops by more than a set margin versus a stored baseline |

Exit criterion: the baseline numbers for the current code are recorded in the repo before any change in A1.

### A1. Fix the text and embedding defects

1. Fix L1 (section 2.1) and add the regression test.
2. Replace the `[:300]` cut with a sentence-aware cut, and keep the full Wikivoyage "Understand" text separately for chunked embedding (see B2).
3. Make the vocabulary a data file, remove weather words from the place vocabulary (L7), and keep photo-condition tags as a separate "mood" factor.
4. Wrap `_embed_photos` per photo in try/except with a counter shown in the summary (L15). Add `pillow-heif` as an optional extra for HEIC.

### A2. Image-to-image matching (the biggest quality lever)

**Why.** Your taste is built from photos. Comparing a photo vector with a text vector crosses modalities, and the similarities are compressed (L4, 0.84 to 0.92 between unrelated destinations). Comparing a photo vector with a photo vector of the destination is a direct comparison and spreads out much more. **[Hypothesis]** until A0 confirms it.

**How.**

1. For each candidate, fetch 3 to 5 hero images (Wikidata P18, Commons category, Wikipedia lead image), downscale to 256 px, and embed them with `embed_image`. Store the mean and the individual vectors in a new table `destination_image_embeddings`.
2. Score = best facet match using image vectors (what you already do with `max` over facets), with the text vector as a secondary term.
3. Keep the text path as fallback when no image exists.
4. This also feeds the design: the page can show "your photo next to the destination photo that matched it" (section 5, D4). One computation, two payoffs.

**Cost.** Images are free downloads (Commons). CLIP vision on CPU is roughly tens of milliseconds per image **[Hypothesis]**. For 600 destinations and 4 images, minutes, once, cached globally (not per user).

### A3. Calibrated scoring

1. Normalise each component per run (z-score or percentile over the candidate pool), then combine with explicit, documented weights. Removes L6.
2. Add a small penalty for strong anti-matches (attribute frequent in the catalog and absent from your history), capped, off by default until A0 shows a gain (L9).
3. Weight trips by engagement: photo count, number of days, recency decay (half-life as a config value). Removes the equal-weight assumption in L8.
4. Fix L5: run all terms (novelty, diversity, climate, season, feedback) in one pass over the full pool, then take the top N. Keep a candidate prefilter only for speed, sized at 200 or more, not 20.

### A4. Structured destination profiles (shared, cached once)

**Why.** Today each destination is described by 300 characters. A structured profile makes matching, filtering, and explaining precise, and it is computed once per destination, not once per user.

| Field | Source | Example |
|---|---|---|
| Vibe scores for the 28+ vocabulary terms (0 to 1) | One cheap-model call per destination, constrained to the vocabulary with JSON schema, fed with Wikivoyage text and POI kinds | beach 0.8, old_town 0.6 |
| Best months and climate band | Open-Meteo (already) | May to Sep |
| Price level | World Bank price-level data by country (B3) | 0.62 of US |
| Typical stay in days | Model estimate, flagged as such | 4 to 7 |
| Family suitability, walkability, base-camp friendliness | Model estimate from Wikivoyage text, flagged as such | high |
| Crowd seasonality | Monthly Wikipedia pageviews (already available API) | peak Aug |

Guardrails: pinned model and prompt, cached by input hash, output validated against the schema, deterministic fallback when the call fails. Fields from a model are labelled "estimated" in the UI.

Approximate cost **[Hypothesis, re-check prices]**: 600 destinations at about 1,500 tokens each on an 8B-class model is well under a dollar, one time.

### A5. Fix popularity and add real novelty

1. Replace the absolute scale with a **percentile within the catalog** (or within the country), so "uncommon" is really the lowest third.
2. Fetch pageviews by exact article title or Wikidata id (B1), and add the sitelink count (number of Wikipedia language editions) as a second signal.
3. Re-run the L3 table as a test fixture: the label distribution must not be more than 60% in one bucket.
4. Add a user-level "adventurousness" value learned from your history (how many of your past trips were low-popularity places) and use it as the default for `--novelty`.

### A6. Traveller context (from the ROADMAP)

Your ROADMAP says you travel with a toddler and want fewer accommodation changes. None of that is used today.

| Input | How it enters ranking |
|---|---|
| Party (adults, child ages) | Hard filter or penalty on destinations with low family suitability (A4) |
| Trip length and pace | Prefer destinations whose typical stay matches and that work from one base |
| Home airport and max travel time | Flight-time estimate from great-circle distance (B3). Hard filter above the limit |
| Budget level | Compare to price level (A4). Soft penalty |
| Season or month window | Uses best months (already built) as a hard or soft filter |
| Passport | Visa friction (B3), optional |

Capture it with a short questionnaire (6 to 8 questions) shown once, then editable on a "Trip brief" panel. Store it per user (ADR 0002) with defaults from past answers.

### A7. Feedback becomes learning

1. Keep `like/save/dislike/skip` as is, but add **reason chips** on dislike ("too touristy", "too far", "not my vibe", "been there"). Reasons are far more useful than the action.
2. Log impressions (what was shown) and the order, so you can compute click and like rates and detect position bias.
3. Learn a per-user vector adjustment: move the taste vector toward liked destination image vectors and away from disliked ones (a Rocchio-style update, simple and deterministic).
4. Keep every recommendation run (fix L12): `run_id` increments, and the UI can show "new since last run".

### A8. The optional smart layer (only after A0 to A5)

The ROADMAP wants an LLM layer. My view, as a peer: do not add it before A1 to A5. A re-ranker given 20 weak candidates cannot repair a weak pool, and it adds cost and non-determinism. When you do add it:

- Input: the top 30 after calibrated scoring, plus your structured profile and trip brief.
- Output: JSON with an order and a one-sentence reason per item, validated against the candidate ids.
- Use it for the "why", for novelty-versus-familiarity judgement, and for "self-contained destination" checks, as the ROADMAP says.
- Gate it behind the A0 metrics: keep it only if it improves Recall@10 on the held-out and triage sets.

You do not need to build a learned ranking model. There is not enough data for one yet.

---

## 4. Workstream B: sources and catalog

**Goal.** Several thousand well-described, correctly identified destinations worldwide, each with a stable id, real photos, and structured facts.

### B1. Stable identity first

Use the **Wikidata QID** as the primary key (`wd:Q...`), with the Wikivoyage title as an attribute. The Wikivoyage API already returns `wikibase_item` (`catalog/fetch.py` `fetch_wikivoyage_page`). Every later lookup (images, pageviews, boundary, climate) must use the QID or the exact title, never a name search. This removes L11 and makes the existing precise-boundary code work: `catalog/regions.py:68` only tries Wikidata P402 for ids that start with `wd:`, but the default catalog uses `wv:`, so that path never runs today **[Code]**.

### B2. Catalog expansion

| Step | Detail |
|---|---|
| **Walk the hierarchy** | Country page, then each region page, then each region's "Cities" and "Other destinations" (nine per list, by Wikivoyage policy). This yields hundreds per country instead of about 20 |
| **Parse templates** | Handle `{{marker}}`, `{{Regionlist}}` and `{{mapshape}}` in wikitext, not only `[[links]]`. Use the `marker` coordinates and Wikidata ids directly (the Italy "Other destinations" section already has `lat`, `long`, `wikidata`) |
| **Fix granularity** | Decide granularity from where a link appears in its own section, not from first-seen order. Drop links to other countries and to the parent (fixes "Hungary" under Croatia) |
| **Global coverage** | Remove `DEFAULT_CANDIDATE_COUNTRIES`. Build the catalog for all countries in the offline `countryInfo.txt`, in batches, cached on disk. The pool and the cost scale with pages fetched, which is free |
| **Quality gate** | Keep a destination only if it has coordinates, a QID, a lead text of at least 200 characters, and at least one image. Log what was dropped |
| **Fallback layers** | GeoNames feature classes (islands, parks, beaches, mountains) from the offline dump for places Wikivoyage does not cover. Optional: Wikidata SPARQL for UNESCO sites (property P1435) and national parks, with Wikivoyage sitelinks |

Note: I did not verify the exact Wikidata class ids for "island" or "national park". Confirm them in a one-day spike before you write the queries.

### B3. New data sources

| Need | Source | Cost | Licence or terms | Effort | Use |
|---|---|---|---|---|---|
| Full destination text | Wikivoyage "Understand", "See", "Do", "Eat", "Get in" sections (same API) | Free | CC BY-SA | S | Chunk and embed per section. Feeds A4 |
| Structured facts | Wikidata (area, population, UNESCO, instance of) | Free | CC0 | S | Filters, granularity |
| POI density by category | OpenStreetMap via Overpass (cache results) or an Overture Maps extract | Free | ODbL, CC BY | M | Counts of beaches, trails, museums, restaurants. Concrete vibe evidence |
| Seasonality of interest | Wikimedia monthly pageviews (already used) | Free | CC0 | S | Peak and quiet months |
| Climate | Open-Meteo (already used). Add the marine API for sea temperature and a Koppen class lookup from the Beck et al. 2018 raster | Free | CC BY 4.0 | S to M | Beach and swim-ability, better best-months |
| Price level | World Bank price level index by country | Free | CC BY 4.0 | S | Budget fit |
| Travel time | OurAirports (open data) plus great-circle distance and a speed model | Free | Public domain | S | Home airport filter. An airline price API (for example Amadeus self-service) is optional and needs a key |
| Safety advice | GOV.UK foreign travel advice (public content API) | Free | OGL | S | Warning flag. Country level only |
| Visa friction | Open passport-index datasets | Free | Check per dataset | S | Optional, needs your passport |
| Community photos | Flickr API, Creative Commons filter, geotagged | Free key | Per photo | M | What travellers photograph in the area. Alternative to Commons for places with few images |
| POI suggestions | OpenTripMap | Free key (daily limit) | ODbL | M | Itinerary POIs beyond Wikivoyage |

Not recommended: scraping TripAdvisor or Google (terms, fragility, as the ROADMAP says), and paid review APIs for now.

### B4. Image sources and licensing

- Commons and Wikidata P18 remain the primary source. Keep attribution and licence per image (already stored).
- **Check before enabling Unsplash.** Their API guidelines ask you to hotlink their CDN URLs and register downloads. The current code downloads and re-serves files **[Hypothesis]**. Read the current terms before you turn it on.
- Openverse results come from arbitrary hosts. Cap download size and mime type before saving.
- Generate and store thumbnails (see D6) and keep the original only for the hero.

### B5. Fix the text shown to you

`fetch_wikipedia_media` uses `explaintext` without `exintro`, so the extract contains `== Heading ==` markers (finding B1 in section 1.2). Strip headings and keep the lead, or request `exintro` plus a separate sections call. This is a one-line fix with high visible effect.

---

## 5. Workstream C: cost optimisation

### C0. Where money and time go today

Absolute spend for one user is small. The reasons to act are waste patterns, privacy, latency, and the open-source future where cost multiplies per user. Do not expect a large saving in dollars for a single archive.

| Cost centre | Today | Tag |
|---|---|---|
| Vision tagging (`ingest --tag`) | 3 photos per trip, one call per trip, `gpt-4o-mini`. Sends original file bytes. No result cache | **[Code]** |
| Re-tagging | Needed to include new trips. Re-sends every trip | **[Code]** |
| Taste enrichment | One text call per trip (cached by tag hash), plus one per "thin" destination | **[Code]** |
| Case writing | DuckDuckGo search plus one model call for each of 20 shortlisted destinations, 5 shown | **[Code]** |
| Itinerary | One model call per guide destination, cached | **[Code]** |
| Explain | Optional, one call per shown destination, cached | **[Code]** |
| External APIs | Sequential calls. 2m11s for 10 destinations with media. Overpass and Nominatim need delays | **[Verified]** |
| Bandwidth | 1280 px originals in 200 px slots. 2.69 MB for 10 cards | **[Verified]** |
| Compute | Full-archive SHA-256 on every ingest. CLIP on CPU for every photo (fine, local) | **[Code]** |

### C1. Vision tagging: biggest lever and a privacy fix

**Problem.** `_encode` reads the original file and sends it base64-encoded. Original files carry EXIF (including GPS and time), and a large JPEG can be several MB. Hosted image models bill by image size tier, so a full-size photo costs several times a downscaled one.

**Illustrative maths (verify against the current OpenRouter model page before you rely on it).** For `gpt-4o-mini` the published scheme counts about 2,833 base tokens plus about 5,667 per 512 px tile in high detail, and the base amount only in low detail. A 12 MP photo in high detail is about 4 tiles, so around 25,000 tokens. In low detail, about 2,800. That is roughly a 9x difference per image.

| Step | Change | Saving |
|---|---|---|
| 1 | Open with Pillow, apply orientation, resize to 512 px on the long side, re-encode JPEG at quality 80, **strip all EXIF**, set `detail: "low"` | Cost about 9x lower per image. Removes GPS leak. Smaller upload |
| 2 | Cache the result per photo hash and prompt version in a new table. Never re-send a known photo | `--retag` stops costing the full archive |
| 3 | Tag trips that have no subjects, not only when the table is empty (fixes C2) | New trips get tagged automatically |
| 4 | Add `--estimate`: print the number of images, the estimated tokens, and the estimated dollars, then ask for confirmation | No surprise bills |
| 5 | Add `monthly_budget_usd` in config. Stop calling hosted models after the limit and say so | Hard ceiling |

### C2. Replace most vision calls with zero-shot CLIP (zero cost, private)

You already compute a CLIP image vector for **every** photo. CLIP can score each photo against short prompts built from the vocabulary ("a photo of a beach", "a photo of mountains", "a photo of a narrow old town street"). **[Hypothesis]** Accuracy for scene-level terms is good, but verify on your persona fixtures (A0).

| Benefit | Detail |
|---|---|
| Cost | Zero marginal cost. No network |
| Privacy | Photos never leave the machine |
| Coverage | Every photo is tagged, not 3 per trip. Fixes the noise in L8 |
| Speed | Text prompts embedded once, then a matrix multiply |

Keep the hosted or local vision model for what CLIP is bad at: activities, food, people and long-tail subjects. Make it opt-in and cheap (C1).

Alternative for the long tail: a local vision-language model on your Mac (for example through Ollama or MLX) for free and private tagging. **[Hypothesis]** Speed and quality need a test on your hardware.

### C3. Move model spend from per-user to per-destination

| Item | Today | Change |
|---|---|---|
| `taste_enrichment` (destination description) | Cached per user | Cache globally by destination and input hash. In the multi-user future, 1,000 users share one result |
| Case, itinerary, structured profile (A4) | Global already for case and itinerary | Keep global. Add the A4 profile |
| Trip attributes | Per user (correct, depends on private photos) | Keep per user, cache by tag hash |

### C4. Do work lazily and in the right order

1. Build cases and guides **after** the final top N is chosen, not for the 20-item shortlist (finding C3 in section 1.2). Saves up to 75% of case calls on the first run.
2. Build the full guide (POIs, books, films, climate, itinerary) when you first open a destination page, in the background, with a skeleton on the page. Do not build it for places you never open.
3. Fetch images in parallel with a small thread pool (4 to 6 workers) and respect per-host rate limits (Nominatim: 1 request per second).
4. Add `Retry-After` and backoff handling for Wikimedia and Overpass.

### C5. Cheaper plumbing

| Item | Change |
|---|---|
| Hashing | Store `(path, size, mtime)` and skip hashing unchanged files (L16) |
| Image serving | Pre-generate 320, 640, 1280 px WebP or AVIF per destination image. Serve with `Cache-Control: public, max-age=31536000, immutable` and a content-hash in the URL. Expected: `/recommendations` from 2.69 MB to roughly 0.3 MB **[Hypothesis]** |
| Model routing | Use a small, cheap model for structured extraction and keep a stronger one only for prose. Pin by name in config (already the pattern). Check the OpenRouter docs for price-sorted provider routing |
| Usage log | Table `llm_usage(feature, model, tokens_in, tokens_out, cost, created_at)`, filled from the response `usage` field. Show a "Costs" panel in settings |
| Prompt size | Send only the fields the prompt needs. Cap `max_tokens` per feature |

### C6. Expected result

| Metric | Now | Target |
|---|---|---|
| Vision cost per trip | Full-size image tier | About one ninth, then near zero with C2 |
| Photos leaving the machine | 3 per trip, with EXIF | 0 by default |
| Case calls on first run | 20 | 5 (then lazy) |
| `/recommendations` payload | 2.69 MB | Under 0.5 MB |
| Time for `recommend` with media (10 items) | 2m11s | Under 40 s with parallel fetch, as an estimate **[Hypothesis]** |
| Surprise spend | Possible | Impossible (`--estimate` and budget cap) |

---

## 6. Workstream D: visual design

**Goal.** A site that feels like a travel magazine built from your own photos, not a dashboard of cards.

### D0. What is wrong now (from the screenshots)

| Observation | Tag |
|---|---|
| Every page is the same beige card with the same orange dash heading | **[Verified]** |
| Destination page is 13 equal cards, 4164 px tall. Nothing leads | **[Verified]** |
| Only one large photo (the hero). Gallery is a small block | **[Verified]** |
| Recommendation row shows a debug chip row (`emb 1.000 attr 0.333`) and a gauge with a number that has no meaning for you | **[Verified]** |
| Profile page is 60 identical small trip cards and a big empty "Visited geography" card | **[Verified]** |
| Map: plain dots, local-language labels, no link from a dot to its page | **[Verified]** |
| Mobile 390 px: horizontal overflow (scrollWidth 455 vs 375), nav clipped, chips collide with the gauge | **[Verified]** |
| Feedback buttons unstyled | **[Verified]** |
| The base CSS is already decent (tokens, dark mode, view transitions, reduced-motion). The problem is structure and imagery, not the palette | **[Code]** |

You do not need to replace the colour system. You need new layouts, more and larger imagery, and a clear visual hierarchy.

### D1. Direction: "photo-first field journal"

| Principle | In practice |
|---|---|
| **Imagery leads** | Full-bleed hero photos, large tiles, photo-derived colour. Text sits on or beside images |
| **Your photos are the proof** | Show your matching photo next to the destination photo (D4). It is the one thing no competitor can show |
| **One accent per page, taken from the hero image** | Extract a dominant colour per destination (Pillow quantise, stored in the DB) and set it as a CSS variable for the page. Each destination feels different. Check contrast (AA) before applying |
| **Depth with intent** | Layered surfaces, soft shadows, glass only on the top bar and overlays, a subtle grain on large gradients. Not on every card |
| **Motion that explains** | Shared-element transition from card image to the destination hero (`view-transition-name` per destination, already half enabled). Scroll-linked hero parallax with `animation-timeline: scroll()` as a progressive enhancement |
| **Editorial type** | Keep the system serif display for titles, add a self-hosted variable serif (for example Fraunces, OFL) and a clean sans for UI. Tabular numbers for data |

### D2. Design tokens

Extend `app.css` (do not rewrite it).

| Token group | Add |
|---|---|
| Colour | `--hero-accent` (per page, from the image), `--surface-1/2/3` elevation steps, semantic colours for like, save, warn. AA contrast checked for light and dark. `--muted` on `--bg` currently needs a check |
| Type scale | A modular scale (1.2) with named steps: `--t-display`, `--t-title`, `--t-body`, `--t-meta` |
| Space and radius | 4 px base grid, three radii. Today radii are 12 and 20 px |
| Motion | Named durations and easing. A single `prefers-reduced-motion` switch |
| Layers | CSS `@layer reset, tokens, base, components, utilities` so overrides stay predictable |

### D3. Page designs

**Home ("Next trip").** Replaces the current home, which is the Taste profile page.

1. Full-width hero: your top recommendation, large photo, one-line reason, match chips, Save and Skip buttons.
2. A row of 4 to 6 more picks as tall image tiles (horizontal scroll on mobile).
3. "Because you loved" strip: 3 of your trips with the recommended places that echo them.
4. A compact "Trip brief" summary (who, when, how long) with an Edit link.

**Explore (was "Recommendations").**

- Grid of image tiles (3 columns desktop, 1 to 2 mobile), not a list of rows. Title and country on the image, one reason line, match badge, like and save icons.
- Left filter rail (collapses to a sheet on mobile): vibe chips, famous or uncommon, season, max flight time, budget, region. Filters update the grid with HTMX and the URL (`hx-push-url`).
- View switch: **Grid | Map | Taste map**. The map view is a split panel with the list. The Taste map is D5.
- Show 24 results at a time with a "Load more" button. Today it shows 5.

**Destination page.** Restructure the 13 cards into five sections with a sticky section bar.

| Section | Content |
|---|---|
| **Overview** | Hero, "decision strip" (match, best months, price level, flight time, vibe chips, Save / Like / Skip), 3-sentence summary, case narrative |
| **Why you** | Your photos next to the matched destination photos (D4), matched attributes, closest trip, reason in plain words. Raw scores behind a "How we scored this" disclosure |
| **Plan** | Itinerary as a day timeline with a map, POIs, when to go (climate and crowd chart in one), practical notes |
| **Media and read** | Gallery as a masonry grid with a keyboard-accessible lightbox, books, films, diaries |
| **More** | Similar destinations, resources, facts. Remove "Destination id" from the user-facing page |

**Taste ("Your taste", was the profile page).**

- Replace the bar lists with a **taste fingerprint**: a radial or ranked chip view of top attributes, plus a world map of where you have been.
- Trips as a **timeline** (year groups, collapsed by default) with a cover photo each, not 60 equal cards.
- "Profile is N photos behind" indicator (from the ROADMAP incremental ingestion item).

**Trip page.** Add a map, the attributes, the recommendations this trip influenced, and previous/next trip links.

### D4. The signature feature: "Why you" with photo pairs

For each recommendation, show 2 to 3 pairs: one of **your** photos and the **destination** photo it matched best (from A2), with a short caption such as "Your Dalmatia trip, 2023". This turns the explanation from text into proof, and it is the clearest answer to "why is this for me". It needs the image-to-image vectors from A2 and nothing else. Do not show raw cosine values.

### D5. Taste map (optional, high impact)

Project photo vectors and destination vectors to 2D with PCA (NumPy, no new dependency). Draw trips as clusters and candidate destinations as points on a canvas or SVG. Hover shows a photo or a destination image. It makes the abstract idea of "taste" visible. Do this after A2, since it needs good vectors. If PCA shows a messy plot, drop it.

### D6. Images and performance

| Item | Change |
|---|---|
| Thumbnails | Generate and cache 320/640/1280 px WebP (or AVIF) for destination images, like `_thumbnail` already does for your photos (480 px) |
| Responsive | `srcset` and `sizes` on all card and gallery images |
| Placeholders | Store a dominant colour or a tiny blur hash per image and use it as the placeholder instead of the shimmer gradient |
| Caching | Long-lived immutable cache headers on content-hashed URLs |
| Lazy sections | Load map, climate, and guide sections with `hx-trigger="revealed"` so first paint is fast |

### D7. Map

- Switch from Leaflet raster tiles with a CSS invert hack to **MapLibre GL** with a vector style, so labels follow your language, dark mode is native, and markers can cluster.
- For offline use, a single PMTiles file (Protomaps) fits the local-first approach. For zero setup, a keyless hosted vector style may exist (for example OpenFreeMap). **[Hypothesis]** Check licence and availability in a spike.
- Marker click opens a small card (photo, name, match, link). Hovering a list item highlights its marker.
- Draw the region polygon on the destination map, fit bounds to the polygon, and cap the minimum zoom so an approximate point is not shown at world scale (observed).

### D8. Accessibility and mobile (fix these regardless)

| Issue | Fix |
|---|---|
| Mobile overflow and clipped nav | Fix the flex wrap, use a bottom tab bar on small screens, `min-width: 0` on grid children, test at 360 px |
| Hero chips overlap the gauge on mobile | Hide the gauge or place it above the title under 660 px |
| Gallery `figure` has a click handler only | Use `<button>`, add focus ring, Escape to close, focus trap, arrow keys |
| Drop cap on every prose block | Only on the lead paragraph of the Overview |
| Text contrast | Run an AA check on `--muted` and `--faint` (light and dark) and fix tokens |
| Motion | Keep the existing `prefers-reduced-motion` handling. Add it to the new parallax |
| Missing favicon | Add one (`/favicon.ico` returns 404, the only console error) |

### D9. Tech choices

| Option | Verdict |
|---|---|
| Keep FastAPI + Jinja + HTMX + Alpine, add MapLibre and a small amount of vanilla JS | **Recommended.** Matches the no-build rule and the local, offline design |
| Add Tailwind | Not needed. Your token CSS is fine and a build step is a cost |
| Rewrite as an SPA (React, Svelte) | Not now. Revisit only if you build the hosted multi-user app and need rich client state |

---

## 7. Workstream E: navigation and interaction

### E0. Problems today

| Problem | Tag |
|---|---|
| Home is the profile. The payoff (recommendations) is one tab away | **[Code]** |
| Three top-level tabs. No search, no saved list, no settings | **[Code]** |
| Only the 3 top-bar links use `hx-boost`. Card and "Explore" links do full page loads | **[Verified]** |
| No previous/next between recommendations, no breadcrumb back with filters preserved | **[Verified]** |
| Map dots do not link to a destination or a trip | **[Verified]** |
| Feedback: GET request that writes (prefetch and crawlers can trigger it), page reload, scroll reset, extra history entry | **[Verified]** |
| Liked and saved places are recorded but you can never see them | **[Code]** |
| "Read-only" dashboard: the main loop (change taste, regenerate) needs a terminal | **[Code]** |
| Recommendations page shows 5 items | **[Code]** |

### E1. New information architecture

| Top-level | Contents |
|---|---|
| **Today** | Next-trip hero, picks, "because you loved" |
| **Explore** | Grid, filters, map and taste-map views, search |
| **Saved** | Board of saved and liked places, compare 2 to 3 side by side, notes, "been there" mark |
| **Your taste** | Fingerprint, trips timeline, trip brief, "N photos behind" |
| **Settings** | Pipeline status (last ingest and recommend, counts), Run buttons, costs panel (C5), API keys status, data export |

Global: search box and a command palette (`/` or Cmd+K) to jump to any destination or trip. On mobile, a bottom tab bar with the first four items.

### E2. Interaction fixes

1. **Feedback as POST via HTMX.** `hx-post` on the buttons, swap the button group in place, show a toast with Undo, no reload. Put the same buttons on every card. Add CSS (`.fb` has none today).
2. **Keep context.** Filters live in the URL. Opening a destination from Explore keeps a "Back to results" link that restores filters and scroll. Add Previous/Next arrows (and swipe on mobile) across the current result set.
3. **Boost everything.** Put `hx-boost` on `<body>` and use `hx-target="main"` with view transitions, so all in-app links navigate without a full reload.
4. **Sticky section bar** on the destination page with scroll-spy (Overview, Why you, Plan, Media, More).
5. **Deep links from the map** to destination and trip pages, and back.
6. **Reason chips** on dislike (A7).
7. **Empty and loading states** with skeletons for slow sections, and a clear next step ("Add photos", "Run recommend") with a button, not a terminal hint.

### E3. Triage mode ("Discover")

A card stack: one large destination image, the match line, and four actions (like, save, skip, not for me). Keyboard arrows on desktop, swipe on mobile. 25 cards take about two minutes and produce the labelled data for A0 and A7. This is the cheapest way to get ground truth and it also works as a fun entry point.

### E4. Run the pipeline from the UI

The web-interface spec forbids mutation from the UI because it needs a worker (`add-web-dashboard` design). At single-user scale you do not need a queue service.

| Step | Detail |
|---|---|
| Job runner | In-process background thread with a single-flight lock and a `jobs` table (id, kind, status, progress, message, timestamps) |
| Endpoints | `POST /jobs/ingest`, `POST /jobs/recommend`, `GET /jobs/{id}` |
| Progress | Server-sent events or HTMX polling every 1 to 2 s, shown in a bar in the top bar |
| Safety | Localhost bind stays. Add a per-start random token in forms for POSTs. The spec scenario "no recomputation on view" still holds: only an explicit button starts work |
| Spec change | Add a new OpenSpec change that replaces the read-only requirement with "explicit, user-started jobs only" |

You do not need Celery, Redis, or a separate worker process for this.

---

## 8. Workstream F: remaining roadmap items

| ROADMAP item | Status now | Plan |
|---|---|---|
| Rich recommendations (description and "why") | Done (evidence-based why, optional LLM prose) | Improve with D4 (photo pairs) and plain-language rewrite of the template (L13) |
| Explicit in-app feedback | Partly done (GET links, consumed by ranking) | E2, A7 |
| Traveller context | Not started | A6 questionnaire and filters |
| Itinerary design | Deterministic split of POIs by day, optional LLM itinerary | See F1 |
| Destination granularity | Tag exists, not used for ranking. Link noise present | B2 (fix noise). Add a granularity boost or filter in A3 |
| Famous vs uncommon | Built but ineffective | A5 |
| Broader catalog and popularity signal | Wikivoyage Europe only | B1 to B3 |
| Smart layer with guardrails | Seams exist (`HostedRanker`, enricher) | A8, after A0 to A5 |
| Structured tagging constrained to the vocabulary | Freeform comma lists plus enrichment | C2 (zero-shot CLIP) and a JSON-schema call for long-tail tags |
| Web app | Done (read-only) | D, E |
| Chat via Telegram or nanobot | Not started | F3 |
| Incremental ingestion and background CLIP | Not started | F2 |
| Open-source readiness, multi-user | User-scoped schema done | F4 |
| Exclusion by proximity only | Done (60 km) | Add a manual "been there" flag in Saved. Keep proximity as default |
| Re-experience vs novelty orientation | Not started | A5 point 4 (learned adventurousness), plus an explicit slider in the trip brief |
| Trip splitting heuristic | Now configurable (gap hours, jump km) | Expose in Settings. Persist trip ids by a stable key (first photo hash) so caches and feedback survive re-clustering (trip ids are positional today) |

### F1. Itinerary design

1. Group POIs into days by geographic clustering (k-means or a greedy nearest-neighbour route on coordinates) so a day stays in one area. Needed for "few accommodation changes".
2. Respect the trip brief: pace (2 to 4 POIs per day with a toddler), opening days if known.
3. Use the LLM only to name days and write the one-line notes, constrained to the given POIs (the current prompt already forbids inventing places).
4. Render as a day timeline with a map per day (E3 Plan section).

### F2. Incremental ingestion

1. File watcher (`watchfiles`) or a poll every N minutes, reusing the `(path, size, mtime)` check from C5.
2. Embedding runs in a background job (E4) and writes per photo.
3. UI shows "N new photos waiting" and a "Process now" button. Profile and recommendations stay usable on the already-embedded photos.

### F3. Chat

Build after A and B. Expose the same core functions behind a small command set: "what should we do in May", "more like Hvar", "cheaper", "with a toddler". The traveller brief (A6) is the shared state. The core already has the ports for it.

### F4. Open-source and multi-user

Defer. When you start: authentication, per-user file storage, a Postgres path (ADR 0002 already allows it), and a job queue. C3 (global destination caches) and C5 (usage log) are the preparation you can do now.

---

## 9. Sequencing

Two tracks can run in parallel because design and logic touch different files.

| Phase | Logic and data track | Design and UX track | Exit criterion |
|---|---|---|---|
| **0. Baseline** (1 to 2 days) | A0 harness, record current metrics | Fix D8 mobile overflow and favicon, style `.fb` | Baseline numbers committed |
| **1. Quick wins** (2 to 4 days) | A1 (L1 fix, wikitext headings, error handling), A5 point 1 and 2, C1 steps 1 to 3, C4 point 1 | E2 POST feedback, boost, Back-to-results | Test for L1 passes. Label distribution under 60% per bucket. Vision payload under 150 KB per image |
| **2. Data foundation** (1 to 2 weeks) | B1 QIDs, B2 hierarchy walk and global coverage, B5 | Saved page, Settings page skeleton | Pool of 3,000 or more destinations with a QID and an image |
| **3. Better matching** (1 to 2 weeks) | A2 image vectors, A3 calibrated scoring, C2 zero-shot CLIP | D4 photo pairs | MRR and Recall@10 beat the baseline on LOTO and personas |
| **4. New look** (2 to 3 weeks) | A4 structured profiles | D1 to D3 new pages, D6 images, D7 map, E1 IA, E3 Discover | Lighthouse performance and accessibility of 90 or more on the three main pages **[Hypothesis]** target |
| **5. Context and learning** (2 weeks) | A6 brief, A7 learning, B3 sources (price, flight time, safety) | E4 run from UI | Triage-set Recall improves over phase 3 |
| **6. Later** | A8 smart layer, F1 itinerary, F2 incremental, D5 taste map | F3 chat | Each gated by its own metric |

Rough sizes: S is under a day, M is 2 to 4 days, L is a week or more. The phases above add up to about 9 to 12 working weeks for one person. Treat that as an estimate, not a commitment.

**Suggested OpenSpec changes** (matches how the project already works):

1. `eval-harness`
2. `fix-clip-text-truncation`
3. `vision-cost-and-privacy` (C1, C4)
4. `catalog-v2` (B1, B2, B5)
5. `popularity-percentile` (A5)
6. `image-matching` (A2)
7. `calibrated-scoring` (A3)
8. `zero-shot-tagging` (C2)
9. `ui-structure-v2` (D1 to D3, E1, E2)
10. `ui-media-and-map` (D6, D7)
11. `run-from-ui` (E4, replaces the read-only requirement)
12. `traveller-brief` (A6)
13. `feedback-learning` (A7)
14. `destination-profiles` (A4)

---

## 10. Risks and open decisions

| Risk or decision | Notes |
|---|---|
| **Image-to-image may not help as much as expected** | A0 decides. Keep the text path as a fallback and the weights configurable |
| **Wider catalog increases noise** | Quality gate in B2 and the A0 metrics catch it. Start with 3 to 5 pilot countries outside Europe |
| **Model-estimated fields can be wrong** (family suitability, stay length) | Label as estimated, keep deterministic fields separate, let you correct them |
| **Licensing of images and data** | Keep per-item attribution (already stored). Check Unsplash terms. ODbL share-alike applies to derived OSM databases, not to your recommendations |
| **Scope** | Design (D, E) is the largest block. If time is short, do phase 0, 1, 2, 3 and the pages in D3 for Explore and Destination only |
| **Decision: PCA taste map** | Fun, but only if vectors are good. Optional |
| **Decision: hosted vision at all** | After C2 you may not need it. Decide after the persona tests |
| **Decision: map stack** | MapLibre with PMTiles (offline) or a hosted keyless style (zero setup) |
| **Decision: what "budget" means** | Country price level is cheap and coarse. Real prices need an API and a key |
| **Where I would push back** | The ROADMAP leans toward a smart LLM layer. The evidence here says data and matching come first. Also, a design refresh before A1 to A3 would polish recommendations that are not yet good |

Note: I assumed one primary user (you), a Mac, and local-first use. If the goal is a hosted multi-user product soon, move C3, C5, and F4 earlier.

---

## 11. Quick Reference

| Area | Do first | Why | Section |
|---|---|---|---|
| Measurement | LOTO eval plus persona fixtures | Nothing else can be judged without it | A0 |
| Bug | Fix 77-token truncation | 14% of destinations are identical to the embedder | 2.1, A1 |
| Catalog | Walk Wikivoyage hierarchy, QIDs, global coverage | About 20 places per country, Europe only | 2.2, B1, B2 |
| Popularity | Percentile labels | 15 of 17 are "famous" | 2.3, A5 |
| Matching | Image-to-image vectors | Direct comparison with your photos | A2 |
| Cost | Downscale, strip EXIF, cache per photo, `--estimate` | Waste and privacy | C1 |
| Cost | Zero-shot CLIP tagging | Free, private, covers all photos | C2 |
| Design | Photo-first pages, 5-section destination page, photo pairs | Page is 13 identical cards | D1 to D4 |
| Navigation | POST feedback, URL filters, Saved, Discover, run from UI | GET writes, no saved list, terminal needed | E1 to E4 |
| Mobile | Fix overflow and nav | Verified broken at 390 px | D8 |

### Related resources

| Resource | Path |
|---|---|
| Existing roadmap | `docs/ROADMAP.md` |
| Architecture decisions | `docs/adr/0001-photo-source-agnostic-core.md`, `docs/adr/0002-user-scoped-data-model.md` |
| Ranking spec | `openspec/specs/recommendation/spec.md` |
| Web spec (read-only requirement to change in E4) | `openspec/specs/web-interface/spec.md` |
| Ranking code | `wanderlens/core/recommend.py`, `wanderlens/pipeline/recommend.py` |
| Embedding code (L1) | `wanderlens/models/embeddings.py` |
| Vision code (C1) | `wanderlens/models/vision.py` |
| Catalog code | `wanderlens/catalog/wikivoyage.py`, `wanderlens/catalog/fetch.py` |
| Styles and templates | `wanderlens/web/static/app.css`, `wanderlens/web/templates/` |
