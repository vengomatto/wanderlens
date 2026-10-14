from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional

import numpy as np

from wanderlens.catalog.destinations import JsonCatalog
from wanderlens.catalog.case import build_case
from wanderlens.catalog.fetch import build_catalog, enrich_records, load_geonames_cities
from wanderlens.core.models import Facet, Recommendation, TasteProfile
from wanderlens.core.recommend import (
    destination_text,
    explain,
    filter_unvisited_proximity,
    rank_destinations,
    taste_attribute_weights,
    taste_embedding,
)
from wanderlens.db import connect, init_db
from wanderlens.pipeline.enrichment import enrich_destination

DEFAULT_CANDIDATE_COUNTRIES = [
    "GR", "HR", "ES", "PT", "CY", "IT", "FR", "TR", "ME", "AL",
    "DE", "AT", "CH", "SI", "NL", "BE", "IE", "GB", "PL", "CZ",
    "SK", "HU", "RO", "BG", "SE", "NO", "DK", "FI", "IS", "MT",
]


def load_taste_embedding(conn: sqlite3.Connection, user_id: int) -> Optional[np.ndarray]:
    rows = conn.execute(
        "SELECT vector FROM photo_embeddings WHERE user_id = ?", (user_id,)
    ).fetchall()
    vectors = [np.frombuffer(row["vector"], dtype=np.float32) for row in rows]
    return taste_embedding(vectors)


def load_taste_facets(
    conn: sqlite3.Connection,
    user_id: int,
    exclude_trip_id: Optional[int] = None,
    min_photos: int = 4,
    recency_half_life_days: float = 0.0,
) -> list[Facet]:
    """One normalized embedding centroid per trip (the taste facets), with the
    trip's label so the closest visit can be named.

    A trip's facet is weighted by ``min(1, n / min_photos)`` so a trip built on
    one or two photos is not treated as a robust centroid, and optionally decays
    by age when a recency half-life is set.
    """
    rows = conn.execute(
        """
        SELECT tp.trip_id AS trip_id, tr.country AS country, tr.city AS city,
               tr.start_at AS start_at, pe.vector AS vector
        FROM trip_photos tp
        JOIN photo_embeddings pe
          ON pe.user_id = tp.user_id AND pe.photo_id = tp.photo_id
        LEFT JOIN trips tr
          ON tr.user_id = tp.user_id AND tr.id = tp.trip_id
        WHERE tp.user_id = ?
        """,
        (user_id,),
    ).fetchall()
    groups: dict[int, list[np.ndarray]] = {}
    labels: dict[int, str] = {}
    started: dict[int, str] = {}
    for row in rows:
        if exclude_trip_id is not None and row["trip_id"] == exclude_trip_id:
            continue
        groups.setdefault(row["trip_id"], []).append(
            np.frombuffer(row["vector"], dtype=np.float32)
        )
        if row["trip_id"] not in labels:
            labels[row["trip_id"]] = (
                ", ".join(p for p in (row["city"], row["country"]) if p)
                or f"trip {row['trip_id']}"
            )
        if row["start_at"]:
            started[row["trip_id"]] = row["start_at"]
    facets: list[Facet] = []
    for trip_id, vectors in groups.items():
        mean = np.mean(np.stack(vectors), axis=0).astype(np.float32)
        norm = np.linalg.norm(mean)
        weight = 1.0 if min_photos <= 0 else min(1.0, len(vectors) / min_photos)
        weight *= _recency_factor(started.get(trip_id), recency_half_life_days)
        facets.append(
            Facet(
                trip_id=trip_id,
                label=labels.get(trip_id, ""),
                vector=mean / norm if norm else mean,
                weight=weight,
            )
        )
    return facets


def _recency_factor(start_at: Optional[str], half_life_days: float) -> float:
    if not start_at or half_life_days <= 0:
        return 1.0
    try:
        started = datetime.fromisoformat(start_at)
    except ValueError:
        return 1.0
    now = datetime.now(timezone.utc)
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    age_days = max(0.0, (now - started).total_seconds() / 86400.0)
    return 0.5 ** (age_days / half_life_days)


def ensure_destination_embeddings(conn, destinations, embedder, model=None):
    """Return {destination_id: vector}, computing and caching missing ones."""
    model = model or getattr(embedder, "cache_key", None) or getattr(embedder, "name", "default")
    cached = {
        row["destination_id"]: np.frombuffer(row["vector"], dtype=np.float32)
        for row in conn.execute(
            "SELECT destination_id, vector FROM destination_embeddings WHERE model = ?", (model,)
        )
    }
    for destination in destinations:
        if destination.id in cached:
            continue
        vector = embedder.embed_text(destination_text(destination))
        cached[destination.id] = vector
        conn.execute(
            "INSERT OR REPLACE INTO destination_embeddings (destination_id, model, dim, vector) "
            "VALUES (?, ?, ?, ?)",
            (destination.id, model, int(vector.shape[0]), vector.astype("float32").tobytes()),
        )
    conn.commit()
    return cached


def load_trip_centers(conn: sqlite3.Connection, user_id: int) -> list[tuple[float, float]]:
    rows = conn.execute(
        "SELECT lat, lon FROM trips WHERE user_id = ? AND lat IS NOT NULL AND lon IS NOT NULL",
        (user_id,),
    ).fetchall()
    return [(row["lat"], row["lon"]) for row in rows]


def load_profile(conn: sqlite3.Connection, user_id: int, embedding=None) -> TasteProfile:
    entries = conn.execute(
        "SELECT factor, key, value FROM profile_entries WHERE user_id = ?", (user_id,)
    ).fetchall()
    geography = {r["key"]: r["value"] for r in entries if r["factor"] == "geography"}
    tags = {r["key"]: r["value"] for r in entries if r["factor"] == "subjects"}
    return TasteProfile(user_id=user_id, geography=geography, tags=tags, embedding=embedding)


def load_feedback(conn: sqlite3.Connection, user_id: int) -> dict[str, str]:
    rows = conn.execute(
        "SELECT destination_id, action FROM feedback WHERE user_id = ?", (user_id,)
    ).fetchall()
    return {row["destination_id"]: row["action"] for row in rows}


def load_feedback_bias(conn: sqlite3.Connection, user_id: int):
    """A deterministic adjustment vector: mean(liked) - mean(disliked) embeddings."""
    rows = conn.execute(
        "SELECT destination_id, action FROM feedback WHERE user_id = ?", (user_id,)
    ).fetchall()
    liked: list = []
    disliked: list = []
    for row in rows:
        vector_row = conn.execute(
            "SELECT vector FROM destination_embeddings WHERE destination_id = ? LIMIT 1",
            (row["destination_id"],),
        ).fetchone()
        if vector_row is None:
            continue
        vector = np.frombuffer(vector_row["vector"], dtype=np.float32)
        if row["action"] in {"like", "save"}:
            liked.append(vector)
        elif row["action"] in {"dislike", "skip"}:
            disliked.append(vector)
    if not liked and not disliked:
        return None

    def mean(vectors):
        mean_vector = np.mean(np.stack(vectors), axis=0).astype(np.float32)
        norm = float(np.linalg.norm(mean_vector))
        return mean_vector / norm if norm else mean_vector

    if liked and disliked:
        bias = mean(liked) - mean(disliked)
    elif liked:
        bias = mean(liked)
    else:
        bias = -mean(disliked)
    norm = float(np.linalg.norm(bias))
    return bias / norm if norm else bias


def _geonames_catalog(
    config, country_codes, limit: int, min_population: int = 50000, providers=None
) -> JsonCatalog:
    cities = config.catalog_path / "cities500.txt"
    if not cities.exists():
        return JsonCatalog([])
    countries = config.catalog_path / "countryInfo.txt"
    records = load_geonames_cities(
        cities,
        country_codes=country_codes,
        min_population=min_population,
        limit=limit,
        countries_path=countries if countries.exists() else None,
    )
    if providers is None:
        from wanderlens.catalog.providers import build_provider_chain

        providers = build_provider_chain(config)
    enrich_records(records, providers=providers)
    return build_catalog({"geonames": records})


def build_catalog_for(
    config, country_codes, cache_path, providers=None, limit: int = 300, min_population: int = 50000
) -> JsonCatalog:
    """Build (and cache) the recommendation catalog for the given country codes.

    Uses the Wikivoyage travel catalog by default, falling back to GeoNames.
    """
    cache = config.catalog_path / cache_path
    if cache.exists():
        return JsonCatalog.load(cache)

    if getattr(config, "catalog_source", "wikivoyage") == "wikivoyage":
        from wanderlens.catalog.fetch import country_names_for_codes
        from wanderlens.catalog.wikivoyage import build_wikivoyage_catalog

        names = country_names_for_codes(config.catalog_path / "countryInfo.txt", country_codes)
        catalog = build_wikivoyage_catalog(
            list(names.values()), min_extract_chars=int(getattr(config, "catalog_min_extract", 0))
        )
        if len(catalog):
            catalog.save(cache)
            return catalog

    catalog = _geonames_catalog(config, country_codes, limit, min_population, providers)
    catalog.save(cache)
    return catalog


def default_catalog(
    config, limit: int = 150, enrich: bool = True, providers=None
) -> JsonCatalog:
    countries = list(getattr(config, "catalog_countries", []) or DEFAULT_CANDIDATE_COUNTRIES)
    return build_catalog_for(
        config, countries, "destinations.json", providers=providers, limit=limit
    )


def run_recommend(
    config,
    user_name: str = "owner",
    count: int = 5,
    embedder=None,
    catalog: Optional[JsonCatalog] = None,
    ranker=None,
    alpha: float = 0.25,
    media: bool = False,
    media_fetcher=None,
    explainer=None,
    diversity: float = 0.0,
    novelty: str = "balanced",
    popularity: bool = False,
    popularity_fetcher=None,
    enricher=None,
    case_searcher=None,
    case_writer=None,
    session=None,
    diagnose: bool = False,
    image_matching: bool = False,
    image_fetcher=None,
    profiles: bool = False,
    profile_writer=None,
) -> list[Recommendation]:
    from wanderlens.pipeline.ingest import get_or_create_user

    conn = connect(config.db_path)
    init_db(conn)
    user_id = get_or_create_user(conn, user_name)

    if enricher is None and getattr(config, "enrich_taste", False) and config.api_key:
        from wanderlens.models.enricher import HostedTasteEnricher

        enricher = HostedTasteEnricher(config.api_key, config.llm_model)

    taste = load_taste_embedding(conn, user_id)
    facets = load_taste_facets(
        conn,
        user_id,
        min_photos=int(getattr(config, "facet_min_photos", 4)),
        recency_half_life_days=float(getattr(config, "recency_half_life_days", 0.0)),
    )
    if not facets and taste is None:
        return []

    if embedder is None:
        if getattr(config, "embedder", "clip") == "synthetic":
            from wanderlens.synthetic import SyntheticEmbedder

            embedder = SyntheticEmbedder()
        else:
            from wanderlens.models.embeddings import OnnxClipEmbedder

            embedder = OnnxClipEmbedder(cache_dir=config.data_dir / "models")

    catalog = catalog or default_catalog(config)
    visited = {
        row["key"]
        for row in conn.execute(
            "SELECT key FROM profile_entries WHERE user_id = ? AND factor = 'geography'", (user_id,)
        )
    }

    candidates = catalog.candidates()
    centers = load_trip_centers(conn, user_id)
    radius = getattr(config, "exclude_radius_km", 60.0)
    from wanderlens.pipeline.brief import filter_by_travel, load_brief

    brief = load_brief(conn, user_id)
    candidates = filter_unvisited_proximity(candidates, centers, radius)
    candidates = filter_by_travel(candidates, brief)
    if enricher is not None:
        candidates = [enrich_destination(conn, user_id, d, enricher) for d in candidates]
    vectors = ensure_destination_embeddings(conn, candidates, embedder)
    image_vectors = None
    if image_matching or image_fetcher is not None:
        from wanderlens.catalog.image_embeddings import ensure_destination_image_embeddings

        image_vectors = ensure_destination_image_embeddings(
            conn, candidates, embedder, fetch_urls=image_fetcher, session=session
        )
    profile = load_profile(conn, user_id, embedding=taste)
    tags = taste_attribute_weights(profile.tags)
    feedback = load_feedback(conn, user_id)
    taste_bias = None
    if getattr(config, "taste_bias_weight", 0.0):
        taste_bias = load_feedback_bias(conn, user_id)

    climate_profile = {}
    climate_enabled = bool(
        getattr(config, "climate", False)
        or getattr(config, "climate_weight", 0.0)
        or getattr(config, "season", "")
    )
    if climate_enabled:
        from wanderlens.pipeline.climate import build_climate_profile, load_climate_profile

        build_climate_profile(conn, user_id, session=session)
        climate_profile = load_climate_profile(conn, user_id)

    shortlist_size = min(
        len(candidates), max(count * 4, int(getattr(config, "candidate_prefilter", 20)))
    )
    shortlist = rank_destinations(
        taste,
        candidates,
        embedder.embed_text,
        top_k=shortlist_size,
        vectors=vectors,
        taste_tags=tags,
        alpha=alpha,
        taste_facets=facets,
        visited_centers=centers,
        feedback=feedback,
        image_vectors=image_vectors,
        calibrate=getattr(config, "calibrate", False),
    )

    shortlist_climate: dict[str, float] = {}
    shortlist_best_months: dict[str, list] = {}
    if climate_profile:
        from wanderlens.pipeline.climate import ensure_destination_climate

        for rec in shortlist:
            try:
                data = ensure_destination_climate(
                    conn, rec.destination, climate_profile, session=session
                )
            except Exception:
                continue
            shortlist_climate[rec.destination.id] = data["match"]
            shortlist_best_months[rec.destination.id] = data["best_months"]

    popularity_scores: dict[str, float] = {}
    if popularity:
        fetcher = popularity_fetcher or _default_popularity_fetcher
        try:
            popularity_scores = fetcher(conn, [rec.destination for rec in shortlist]) or {}
        except Exception:
            popularity_scores = {}

    recommendations = rank_destinations(
        taste,
        [rec.destination for rec in shortlist],
        embedder.embed_text,
        top_k=count,
        vectors=vectors,
        taste_tags=tags,
        alpha=alpha,
        taste_facets=facets,
        visited_centers=centers,
        diversity=diversity,
        novelty=novelty,
        popularity=popularity_scores,
        feedback=feedback,
        climate=shortlist_climate or None,
        climate_weight=getattr(config, "climate_weight", 0.0),
        season=(getattr(config, "season", "") or brief.get("season", "")) or None,
        best_months=shortlist_best_months or None,
        image_vectors=image_vectors,
        calibrate=getattr(config, "calibrate", False),
        taste_bias=taste_bias,
        taste_bias_weight=getattr(config, "taste_bias_weight", 0.0),
        anti_match_weight=getattr(config, "anti_match_weight", 0.0),
    )

    if diagnose:
        from wanderlens.core.evaluate import diagnostics

        report = diagnostics(list(vectors.values()), recommendations)
        print(f"[diagnose] {report}")

    if case_searcher is not None or case_writer is not None:
        for rec in recommendations:
            try:
                build_case(
                    conn,
                    rec.destination,
                    searcher=case_searcher,
                    writer=case_writer,
                )
            except Exception:
                continue

    if profiles or profile_writer is not None:
        from wanderlens.catalog.profiles import build_profile

        for rec in recommendations:
            try:
                build_profile(conn, rec.destination, writer=profile_writer)
            except Exception:
                continue

    visited_country = (
        max(profile.geography, key=profile.geography.get) if profile.geography else None
    )
    if ranker is not None:
        recommendations = ranker.rank(recommendations, profile)
    else:
        for rec in recommendations:
            rec.explanation = _explain(
                conn, user_id, rec, profile, visited_country, explainer
            )

    run_id = conn.execute(
        "SELECT COALESCE(MAX(run_id), 0) + 1 FROM recommendations WHERE user_id = ?", (user_id,)
    ).fetchone()[0]
    now = datetime.now(timezone.utc).isoformat()
    for rec in recommendations:
        destination = rec.destination
        conn.execute(
            "INSERT INTO recommendations "
            "(user_id, run_id, rank, destination_id, score, explanation, "
            " destination_name, destination_country, destination_lat, destination_lon, "
            " destination_description, embedding_score, attribute_score, "
            " matched_attributes, best_trip_id, best_trip_label, best_facet_similarity, "
            " nearest_trip_km, popularity, popularity_label) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                run_id,
                rec.rank,
                destination.id,
                rec.score,
                rec.explanation,
                destination.name,
                destination.country,
                destination.lat,
                destination.lon,
                destination.description,
                rec.embedding_score,
                rec.attribute_score,
                json.dumps(rec.matched_attributes),
                rec.best_trip_id,
                rec.best_trip_label,
                rec.best_facet_similarity,
                rec.nearest_trip_km,
                rec.popularity,
                rec.popularity_label,
            ),
        )
        conn.execute(
            "INSERT OR REPLACE INTO impressions "
            "(user_id, run_id, destination_id, rank, shown_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, run_id, destination.id, rec.rank, now),
        )
    conn.execute(
        "DELETE FROM recommendations WHERE user_id = ? AND run_id <= ?", (user_id, run_id - 10)
    )
    conn.commit()

    if media:
        fetcher = media_fetcher or _default_media_fetcher
        try:
            fetcher(conn, recommendations, config)
        except Exception:
            pass
    return recommendations


def _evidence(rec: Recommendation, visited_country: Optional[str]) -> dict:
    return {
        "destination": rec.destination.name,
        "country": rec.destination.country,
        "closest_trip": rec.best_trip_label,
        "similarity": round(rec.best_facet_similarity, 3)
        if rec.best_facet_similarity is not None
        else None,
        "shared_attributes": sorted(
            rec.matched_attributes, key=lambda key: -rec.matched_attributes[key]
        ),
        "new_for_you": rec.nearest_trip_km is not None,
        "nearest_visit_km": round(rec.nearest_trip_km)
        if rec.nearest_trip_km is not None
        else None,
        "visited_country": visited_country,
        "embedding_score": round(rec.embedding_score, 3)
        if rec.embedding_score is not None
        else None,
        "attribute_score": round(rec.attribute_score, 3)
        if rec.attribute_score is not None
        else None,
    }


def _evidence_hash(evidence: dict) -> str:
    payload = json.dumps(evidence, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _explain(conn, user_id, rec, profile, visited_country, explainer) -> str:
    fallback = explain(rec, profile, visited_country)
    if explainer is None:
        return fallback
    evidence = _evidence(rec, visited_country)
    digest = _evidence_hash(evidence)
    try:
        row = conn.execute(
            "SELECT text FROM recommendation_explanations "
            "WHERE user_id = ? AND destination_id = ? AND evidence_hash = ?",
            (user_id, rec.destination.id, digest),
        ).fetchone()
        if row is not None:
            return row["text"]
        text = (explainer.synthesize(evidence) or "").strip()
        if not text:
            return fallback
        conn.execute(
            "INSERT OR REPLACE INTO recommendation_explanations "
            "(user_id, destination_id, evidence_hash, model, prompt_version, text, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                rec.destination.id,
                digest,
                getattr(explainer, "model", ""),
                getattr(explainer, "prompt_version", ""),
                text,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        return text
    except Exception:
        return fallback


def _default_media_fetcher(conn, recommendations, config) -> int:
    from wanderlens.catalog.media import build_media_chain, fetch_media_for

    chain = build_media_chain(
        sources=getattr(config, "media_sources", []),
        keys={
            "unsplash": getattr(config, "unsplash_key", None),
            "pexels": getattr(config, "pexels_key", None),
        },
    )
    return fetch_media_for(
        conn,
        recommendations,
        config.data_dir / "media",
        chain=chain,
        refresh=getattr(config, "refresh_media", False),
    )


def _default_popularity_fetcher(conn, destinations) -> dict:
    from wanderlens.catalog.popularity import fetch_popularity_for

    return fetch_popularity_for(conn, destinations)


def run_ingest_job(config, user_name: str = "owner"):
    """Ingest photos and rebuild the profile (used by the dashboard job runner)."""
    from wanderlens.pipeline.ingest import run_ingest
    from wanderlens.pipeline.profile import run_profile

    run_ingest(config, user_name=user_name)
    return run_profile(config, user_name=user_name)
