# Wanderlens assessment after the improvement plan

Date: 2026-10-14. Code reviewed: `9f97a56` (main). Compared against: `docs/IMPROVEMENT_PLAN.md` (written against `208ce58`).

---

## 0. How to read this

You pulled about 18 changes made after the plan. This document checks which plan items landed, whether they work, and what broke. It does not propose a new plan. Section 6 gives a suggested order for the fixes.

| Tag | Meaning |
|---|---|
| **[Verified]** | I ran it and measured the result |
| **[Code]** | Read in the source, not executed |

**Method**

1. Pulled `main` (`208ce58` to `9f97a56`, 170 files, about 6,700 lines added).
2. Ran the full test suite, the new evaluation harness, and the real CLIP text model against the new encoder.
3. Re-ran the Wikivoyage catalog builder and the pageview code on live data (7 to 8 countries).
4. Served the dashboard on a scratch copy outside the repo, took screenshots (desktop, mobile, light, dark), clicked through the new features, and measured payloads.
5. Read the diffs of the ranking, jobs, tagging, image-matching, and re-ranker code.

Note: the synthetic embedder makes `emb` equal 1.000 for every card, so these runs say nothing about taste quality. Image-matching quality, the hosted re-ranker, and the profile writer were **not** tested.

Note: upstream `docs/IMPROVEMENT_PLAN.md` is byte-identical to the plan I wrote. It was committed in `5ae7d8a`.

---

## 1. Summary

The logic and cost fixes largely hold up. The catalog rewrite made live data worse. Most new ranking features are off by default. The UI gained features but not the visual redesign, and two new bugs block normal use.

| Area | Verdict |
|---|---|
| Embedding bug (L1) | Fixed |
| Vision cost and privacy (C1) | Fixed |
| Tagging cost (C2) | Mostly done (local zero-shot CLIP is the default) |
| Evaluation harness (A0) | Built, but the gate cannot fail |
| Popularity label (A5) | Label fixed, novelty bias not |
| Catalog (B1, B2) | **Regressed** |
| Scoring features (A2, A3, A7) | Built, **off by default** |
| Design (D) | Mostly not done |
| Navigation (E) | Partly done, **two blocking bugs** |

---

## 2. What is fixed and confirmed

| Item | Before | After | Tag |
|---|---|---|---|
| Tests | 256 passed, 1 skipped | 328 passed, 1 skipped (5.8 s) | **[Verified]** |
| CLIP 77-token bug | Hvar, Zermatt, Kyoto at cosine 0.9999 | 0.933 to 0.959. Cache key now ends in `-textv2`, so old vectors recompute | **[Verified]** |
| Vision upload | Original bytes with EXIF | 4000x3000 JPEG with GPS (3.47 MB) became 110,913 bytes at 512x384, 0 EXIF tags. `detail: "low"` set | **[Verified]** |
| Tag cache | None. New trips needed `--retag` | `tag_cache` keyed on the sampled photos' hashes. New trips tagged on the next `--tag` run | **[Verified]** |
| Tagging default | Hosted vision model | Local zero-shot CLIP (`tag_provider: clip`). Hosted model needs `--vlm` | **[Verified]** |
| Case building | 20 destinations, 5 shown | Final N only | **[Verified]** |
| Run history | Table wiped every run, `run_id` always 1 | `run_id` increments, last 10 kept, views read the latest run | **[Verified]** |
| Famous or uncommon label | 15 of 17 "famous" | 6 famous, 5 balanced, 6 uncommon on the same 17 titles. Cres, Magnesia, Kvarner now "uncommon" | **[Verified]** |
| Evaluation | One hold-out trip, saturated synthetic gallery | Leave-one-trip-out over all geotagged trips. Prints MRR, Recall@10, Recall@50. `--diagnose` prints component spread and collapsed share | **[Verified]** |
| POST feedback with reasons | GET link, reload | HTMX POST, no reload, scroll and URL kept. Reason chips work | **[Verified]** |
| Explore grid | Row list | 3-column image tiles with Grid or List toggle | **[Verified]** |
| Map marker links | None | Marker popups link to a page | **[Verified]** (trip marker only) |

---

## 3. Regressions and bugs

Ordered by severity.

### 3.1 Blocking

| # | Bug | Evidence | Cause | Tag |
|---|---|---|---|---|
| 1 | **Home page wipes itself.** `/` loads, then the whole page is replaced by "No jobs yet." The taste profile and the job buttons are unreachable | Screenshot and DOM check | The Pipeline card poller (`profile.html:82`) has no `hx-target`, so it inherits `hx-target="main"` from `<body>` and overwrites `<main>` | **[Verified]** |
| 2 | **A failed UI job locks the database.** The job stays "running 10%" forever. Every later `POST .../feedback` returns 500 until the server restarts | Job failed (the scratch venv lacked `tokenizers`), then `sqlite3.OperationalError: database is locked` while recording the error | Not traced. Likely the job's own open connection holds a write lock while `JobRunner._update` opens a second connection | **[Verified]** (effect), cause is a reading of `web/jobs.py` |
| 3 | **Destination ids with `/` return 404.** The page, its image, and its feedback POST all fail | `wv:London/Wandsworth`. In Discover this card was first, so a like did nothing and Saved stayed at 0 | The route `{destination_id}` does not accept `/`, and the `urlencode` filter leaves `/` unescaped | **[Verified]** |
| 4 | **Catalog regression on live data** (see 3.2) | See below | Marker templates keep raw markup | **[Verified]** |

### 3.2 Catalog v2

| Metric | Before (`208ce58`) | After (`9f97a56`) |
|---|---|---|
| Destinations, 7 countries | 140 | **78** |
| Texts over 77 tokens | 14% | 0% |
| Entries with empty description | 0 | 75 of 78 under 60 characters. Italy: 18 of 18 empty |
| Names from marker templates | Clean | `[[Rome]]`, `[[Alps`, `[[Barcelona]]` in names, ids, and URLs |
| Croatia noise ("Hungary", "Bosnia") | Present | Gone |
| Italy cities | 0 | 9 |
| Portugal | 20 | 4 |
| Albania | 10 | 2 |

**Why it happens.** `_template_entry` returns the raw `name=[[Rome]]` value. The `<title>` then flows into `fetch_pages`, ids, and `article_title`. Pages without coordinates are dropped, which removes 11 entries for Portugal and 15 for Albania.

**Visible symptoms in the dashboard.**

- "London/Wandsworth" ranked **#1 under Malta**.
- "Golden Bay (Malta)" resolved to a New Zealand page, 18,197 km away.
- Pageview lookups fail for bracketed titles, so popularity stays unset for those entries.

**Not delivered.**

- The region hierarchy walk is not implemented. The default catalog is about 10 destinations per country.
- Global coverage is only opt-in through `catalog_countries`. The default is still the 30 European countries.
- Descriptions are still cut at `[:300]`.

**Why the tests passed.** `tests/test_wikivoyage.py` uses plain `[[Link]]` fixtures, not real marker wikitext.

### 3.3 Other defects

| # | Defect | Tag |
|---|---|---|
| 5 | **Eval gate cannot fail.** `docs/eval-baseline.json` records MRR 0.001 and the check is `mrr >= baseline - 0.05`. LOTO also ranks with defaults only, so it does not measure image matching or calibration. `eval --synthetic` is still saturated at 1.00 | **[Verified]** |
| 6 | **CSRF only on jobs.** `POST /jobs/*` checks a token. `POST /destinations/{id}/feedback` and `POST /brief` do not, so any web page open in your browser can submit them while the server runs on localhost. Impact is low (taste data), but the pattern is inconsistent | **[Code]** |
| 7 | **UI jobs differ from CLI runs.** The job calls `run_recommend(count=8, media=True, popularity=True)`. The CLI also sets diversity 0.25, case writer, explainer. Same button, different results | **[Code]** |
| 8 | **Job progress is fake.** Fixed at 10, then 100. No real stages | **[Code]** |
| 9 | **Zero-shot `old_town` label adds a spurious `city` attribute.** The vocabulary splits `old_town` into `old` and `town`, and `town` is a `city` synonym. The `weather` label yields no attribute | **[Verified]** |
| 10 | **Lightbox.** Escape does not close it. Gallery `<figure>` has no `tabindex` or role | **[Verified]** |
| 11 | **Discover keyboard.** Only ArrowLeft and ArrowRight work, and they advance without recording anything | **[Verified]** |
| 12 | **Explore overflows at 390 px** (`scrollWidth` 409 vs 375), caused by the Grid or List toggle. Five nav links wrap into two rows, no bottom bar | **[Verified]** |
| 13 | **Console 404** for the broken image of the slash id | **[Verified]** |
| 14 | **`--estimate` is inexact.** Fixed 1,500 tokens per image at $0.15 per million, and it counts trips already cached | **[Code]** |

---

## 4. Built but off by default

A default run gets the L1 fix, cheaper tagging, percentile labels, and the other fixes in section 2. It gets none of the new matching or scoring work.

| Feature | Default | Switch |
|---|---|---|
| Image-to-image matching | Off | `--image-matching` |
| Score calibration | Off | `--calibrate` |
| Anti-match penalty | Off (weight 0) | `anti_match_weight` |
| Recency weighting | Off (half-life 0) | `recency_half_life_days` |
| Learned taste bias | Off (weight 0) | `taste_bias_weight` |
| Structured destination profiles | Off | `--profiles` |
| Hosted re-ranker | Off | `--rerank` |
| Single-pass ranking | Not built. Two passes remain, prefilter 20 | `candidate_prefilter` |

**Weaknesses to fix before you turn them on** (all **[Code]**).

| Feature | Weakness |
|---|---|
| Image matching | Destinations with images are scored image-to-image. Those without are scored text-to-image in the same pool. The two cosine ranges differ, so the mix biases the order. Calibration (`min-max` over the pool) does not remove a modality bias |
| Image matching | `ensure_destination_image_embeddings` runs the full media chain (about 6 to 10 requests) for every candidate, sequentially, and downloads 1280 px originals. A 3,000-place catalog would take a long time |
| Image matching | Diversity (MMR) still uses the text vectors |
| Re-ranker | Sends only names and visited countries. No id validation, no caching, no scores in the prompt. This is not the guarded design in plan section A8 |
| Calibration | `min-max` is sensitive to outliers and makes scores pool-relative. Fine for ordering, not for the displayed "match" number |
| Novelty | The bias term still uses the absolute pageview score (`pop - 0.5`). Only the label is percentile-based. `--novelty uncommon` stays weak |

---

## 5. Plan items still open or only partly done

### 5.1 Logic and cost

| Plan item | Status | Note |
|---|---|---|
| A1 vocabulary: remove weather words from places | Not done | `core/vocabulary.py` unchanged |
| A3 single-pass scoring over the full pool | Not done | Prefilter still 20 by default |
| A4 structured destination profiles | Built, off | `--profiles` |
| A5 popularity by exact article or QID | Open | Marker entries make it worse (see 3.2) |
| A6 traveller brief | Partial | Fields and distance filter exist. Season feeds ranking. Party and pace are stored but not used for ranking, as far as I read **[Code]** |
| A8 guarded re-ranker | Not done | See section 4 |
| C1 budget cap and `llm_usage` table | Not done | `grep` finds neither |
| C2 tag every photo | Not done | Zero-shot still tags 3 sampled photos per trip (`sample_per_trip=3`) **[Code]** |
| C4 parallel fetching, rate limits | Not verified | No change seen in `media.py` |
| C5 image thumbnails, immutable cache headers | Not done | See 5.2 |
| C5 skip hashing unchanged files | Not verified | |

### 5.2 Design and navigation

| Plan item | Status | Evidence |
|---|---|---|
| D1 photo-first direction | Partial | Explore grid only |
| D2 design tokens | Not done | `app.css` +110 lines, no new token groups |
| D3 Home "Next trip" | Not done | Home is still the profile, and it is broken (bug 1) |
| D3 Explore grid | Done, no filters | Name search only. Client-side, URL does not change |
| D3 Destination page restructure | Not done | 14 stacked cards, 5,074 px tall (was 4,164 px) |
| D3 Taste and trip pages | Partial | Brief form added. Trip page is still photos only |
| D4 photo pairs ("your photo next to theirs") | Not done | No pair markup in the DOM |
| D5 taste map | Not done | |
| D6 thumbnails and `srcset` | Not done | Explore: 2.57 MB, 13 requests, 1,023 to 1,280 px originals (up to 520 KB) in 337 px slots. Destination page: 3.6 to 4.0 MB, 30+ requests, a 950 KB gallery image |
| D7 MapLibre | Not done | Still Leaflet raster. Marker links added |
| D8 mobile and accessibility | Partial | Favicon added. Items 10 and 12 in section 3.3 remain |
| E1 information architecture | Partial | Saved and Discover added. No search, no settings page. Top bar has 5 links |
| E2 POST feedback | Done | No toast or undo |
| E2 boost, back-to-results, prev/next | Partial | Boost added. No prev/next, no URL-based filters |
| E3 Discover | Partial | Click works. Keyboard actions missing. First card's feedback 404s in the test data |
| E4 run from UI | Broken | Token-protected POST works. Home wipes itself and a failed job locks the DB |

**Visual verdict.** Only Explore changed visually. The destination page still uses the same beige card 14 times. Recommendation cards still show `emb 0.000 / attr 0.000` chips and the gauge. Dark mode is the same layout inverted. The photo-first direction in the plan is mostly still to do.

---

## 6. Suggested order

### 1. Fix the blocking bugs (about 1 day)

1. Add `hx-target="this"` (or the card id) to the Pipeline poller. Set `hx-target` explicitly on every HTMX element that sits inside `<body hx-target="main">`.
2. Open the job's DB connection with a timeout and close every connection in `run_recommend` and `run_ingest_job`. Add a test that fails a job and then posts feedback.
3. Allow `/` in destination ids: use `{destination_id:path}` on the routes and `urlencode(safe="")` in templates. Better: decide whether ids with a slash should exist at all.

### 2. Fix the catalog (2 to 4 days)

1. Strip wiki markup from marker values (`[[A]]`, `[[A|B]]`, trailing `#fragment`). Use the `wikidata=` value as the QID.
2. Add a test with real marker wikitext (Italy "Cities" and "Other destinations" are good fixtures).
3. Add the quality gate from plan B2 and print what was dropped.
4. Then implement the region hierarchy walk and remove the 30-country default.

You do not need to add new data sources until the walk works.

### 3. Make evaluation meaningful (1 day)

1. Record a real baseline and a failing threshold relative to it (for example, fail if Recall@10 drops by 10% relative, not 0.05 absolute).
2. Run LOTO once per feature flag set and print a table.
3. Replace the saturated synthetic gallery with the persona fixtures from plan A0.

### 4. Decide defaults for the built features (1 to 2 days)

1. Fix the image and text mixing (score the whole pool in one modality, or normalise per modality).
2. Run LOTO with each flag. Turn on only what improves Recall@10.
3. Bound image fetching: shortlist only, 256 px thumbnails, a thread pool, and reuse the downloads for the media step.

### 5. Do the design work

1. Destination page: five sections, sticky section bar, photo pairs from the image vectors you now have.
2. Thumbnails, `srcset`, long cache headers.
3. Mobile bottom bar, fix Explore overflow.
4. Home "Next trip" hero once the home bug is fixed.

### 6. Small items

CSRF token on feedback and brief, real job progress, Discover keyboard actions, lightbox keyboard access, `old_town` label alias, budget cap and `llm_usage` table.

---

## 7. Risks and decisions

| Item | Note |
|---|---|
| **Defaults versus experiments** | Decide whether new features stay opt-in until LOTO shows a gain. I recommend yes. Today a user cannot get the improved ranking without knowing five flags |
| **Gate strictness** | A gate that cannot fail gives false confidence. Fix it before relying on it for the defaults |
| **Pace of change** | 18 changes in a day with tests passing but live data regressed. Add one smoke test against real Wikivoyage wikitext and one against a recorded API response for each new fetcher |
| **Slash ids** | Wikivoyage titles can contain `/`. Treat ids as opaque, or encode them at creation |
| **UI jobs** | Same button should give the same result as the CLI. Move the option set into one function used by both |
| **Not tested here** | Image-matching quality on real photos, the hosted re-ranker, the profile writer, the traveller brief effect on ranking, real LLM cost |

---

## 8. Quick Reference

| Area | Status | Next action | Section |
|---|---|---|---|
| Embedding truncation | Fixed | None | 2 |
| Vision cost and privacy | Fixed | Add budget cap and usage log | 2, 5.1 |
| Evaluation | Built, gate cannot fail | Real baseline, flag matrix | 3.3, 6.3 |
| Popularity | Label fixed, bias not | Percentile in the bias term | 4 |
| Catalog | Regressed | Strip markup, test, hierarchy walk | 3.2, 6.2 |
| Image matching, calibration | Built, off | Fix modality mix, evaluate, decide defaults | 4, 6.4 |
| Re-ranker | Weak | Add validation and cache, gate on LOTO | 4 |
| Home page | Broken | `hx-target` | 3.1, 6.1 |
| Job failures | Lock the DB | Close connections, timeout | 3.1, 6.1 |
| Slash ids | 404 | `:path` routes, `urlencode(safe="")` | 3.1, 6.1 |
| Destination page | Unchanged look | Five sections, photo pairs | 5.2, 6.5 |
| Images | 1,280 px in 337 px slots | Thumbnails, `srcset` | 5.2, 6.5 |
| Mobile | Overflow, no bottom bar | Fix toggle, add bar | 3.3, 6.5 |

### Related resources

| Resource | Path |
|---|---|
| Original plan | `docs/IMPROVEMENT_PLAN.md` |
| Roadmap | `docs/ROADMAP.md` |
| Evaluation baseline and script | `docs/eval-baseline.json`, `scripts/eval.sh` |
| Catalog builder | `wanderlens/catalog/wikivoyage.py` |
| Jobs and routes | `wanderlens/web/jobs.py`, `wanderlens/web/app.py` |
| Home template (bug 1) | `wanderlens/web/templates/profile.html`, `base.html` |
| Ranking | `wanderlens/core/recommend.py`, `wanderlens/pipeline/recommend.py` |
| Image matching | `wanderlens/catalog/image_embeddings.py` |
| Zero-shot tagging | `wanderlens/models/tagging.py`, `wanderlens/core/vocabulary.py` |
