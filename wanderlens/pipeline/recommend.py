from __future__ import annotations

import sqlite3
from typing import Optional

import numpy as np

from wanderlens.catalog.destinations import JsonCatalog
from wanderlens.catalog.fetch import build_catalog, enrich_records, load_geonames_cities
from wanderlens.core.models import Recommendation, TasteProfile
from wanderlens.core.recommend import (
    destination_text,
    explain,
    filter_unvisited_proximity,
    rank_destinations,
    taste_attribute_weights,
    taste_embedding,
)
from wanderlens.db import connect, init_db

DEFAULT_CANDIDATE_COUNTRIES = ["GR", "HR", "ES", "PT", "CY", "IT", "FR", "TR", "ME", "AL"]


def load_taste_embedding(conn: sqlite3.Connection, user_id: int) -> Optional[np.ndarray]:
    rows = conn.execute(
        "SELECT vector FROM photo_embeddings WHERE user_id = ?", (user_id,)
    ).fetchall()
    vectors = [np.frombuffer(row["vector"], dtype=np.float32) for row in rows]
    return taste_embedding(vectors)


def load_taste_facets(
    conn: sqlite3.Connection, user_id: int, exclude_trip_id: Optional[int] = None
) -> list[np.ndarray]:
    """One normalized embedding centroid per trip (the taste facets)."""
    rows = conn.execute(
        """
        SELECT tp.trip_id AS trip_id, pe.vector AS vector
        FROM trip_photos tp
        JOIN photo_embeddings pe
          ON pe.user_id = tp.user_id AND pe.photo_id = tp.photo_id
        WHERE tp.user_id = ?
        """,
        (user_id,),
    ).fetchall()
    groups: dict[int, list[np.ndarray]] = {}
    for row in rows:
        if exclude_trip_id is not None and row["trip_id"] == exclude_trip_id:
            continue
        groups.setdefault(row["trip_id"], []).append(
            np.frombuffer(row["vector"], dtype=np.float32)
        )
    facets: list[np.ndarray] = []
    for vectors in groups.values():
        mean = np.mean(np.stack(vectors), axis=0).astype(np.float32)
        norm = np.linalg.norm(mean)
        facets.append(mean / norm if norm else mean)
    return facets


def ensure_destination_embeddings(conn, destinations, embedder, model=None):
    """Return {destination_id: vector}, computing and caching missing ones."""
    model = model or getattr(embedder, "name", "default")
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
        catalog = build_wikivoyage_catalog(list(names.values()))
        if len(catalog):
            catalog.save(cache)
            return catalog

    catalog = _geonames_catalog(config, country_codes, limit, min_population, providers)
    catalog.save(cache)
    return catalog


def default_catalog(
    config, limit: int = 150, enrich: bool = True, providers=None
) -> JsonCatalog:
    return build_catalog_for(
        config, DEFAULT_CANDIDATE_COUNTRIES, "destinations.json", providers=providers, limit=limit
    )


def run_recommend(
    config,
    user_name: str = "owner",
    count: int = 5,
    embedder=None,
    catalog: Optional[JsonCatalog] = None,
    ranker=None,
    alpha: float = 0.5,
) -> list[Recommendation]:
    from wanderlens.pipeline.ingest import get_or_create_user

    conn = connect(config.db_path)
    init_db(conn)
    user_id = get_or_create_user(conn, user_name)

    taste = load_taste_embedding(conn, user_id)
    facets = load_taste_facets(conn, user_id)
    if not facets and taste is None:
        return []

    if embedder is None:
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
    candidates = filter_unvisited_proximity(candidates, centers, radius)
    vectors = ensure_destination_embeddings(conn, candidates, embedder)
    profile = load_profile(conn, user_id, embedding=taste)
    recommendations = rank_destinations(
        taste,
        candidates,
        embedder.embed_text,
        top_k=count,
        vectors=vectors,
        taste_tags=taste_attribute_weights(profile.tags),
        alpha=alpha,
        taste_facets=facets,
    )

    if ranker is not None:
        recommendations = ranker.rank(recommendations, profile)
    else:
        visited_country = (
            max(profile.geography, key=profile.geography.get) if profile.geography else None
        )
        for rec in recommendations:
            rec.explanation = explain(rec.destination, profile, visited_country)

    conn.execute("DELETE FROM recommendations WHERE user_id = ?", (user_id,))
    for rec in recommendations:
        conn.execute(
            "INSERT INTO recommendations (user_id, run_id, rank, destination_id, score, explanation) "
            "VALUES (?, 1, ?, ?, ?, ?)",
            (user_id, rec.rank, rec.destination.id, rec.score, rec.explanation),
        )
    conn.commit()
    return recommendations
