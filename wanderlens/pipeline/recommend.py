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


def load_profile(conn: sqlite3.Connection, user_id: int, embedding=None) -> TasteProfile:
    entries = conn.execute(
        "SELECT factor, key, value FROM profile_entries WHERE user_id = ?", (user_id,)
    ).fetchall()
    geography = {r["key"]: r["value"] for r in entries if r["factor"] == "geography"}
    tags = {r["key"]: r["value"] for r in entries if r["factor"] == "subjects"}
    return TasteProfile(user_id=user_id, geography=geography, tags=tags, embedding=embedding)


def default_catalog(
    config, limit: int = 150, enrich: bool = True, description_fetcher=None
) -> JsonCatalog:
    cache = config.catalog_path / "destinations.json"
    if cache.exists():
        return JsonCatalog.load(cache)
    cities = config.catalog_path / "cities500.txt"
    if not cities.exists():
        return JsonCatalog([])
    countries = config.catalog_path / "countryInfo.txt"
    records = load_geonames_cities(
        cities,
        country_codes=DEFAULT_CANDIDATE_COUNTRIES,
        min_population=50000,
        limit=limit,
        countries_path=countries if countries.exists() else None,
    )
    if enrich:
        enrich_records(records, fetch=description_fetcher)
    catalog = build_catalog({"geonames": records})
    catalog.save(cache)
    return catalog


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
    if taste is None:
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
    vectors = ensure_destination_embeddings(conn, candidates, embedder)
    candidates = catalog.candidates()
    vectors = ensure_destination_embeddings(conn, candidates, embedder)
    profile = load_profile(conn, user_id, embedding=taste)
    recommendations = rank_destinations(
        taste,
        candidates,
        embedder.embed_text,
        exclude_countries=visited,
        top_k=count,
        vectors=vectors,
        taste_tags=taste_attribute_weights(profile.tags),
        alpha=alpha,
    )

    if ranker is not None:
        recommendations = ranker.rank(recommendations, profile)
    else:
        visited_country = next(iter(visited), None)
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
