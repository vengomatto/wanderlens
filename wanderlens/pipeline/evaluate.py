from __future__ import annotations

from collections import Counter
from typing import Optional

from wanderlens.catalog.destinations import JsonCatalog
from wanderlens.catalog.fetch import country_code_for_name
from wanderlens.core.evaluate import evaluate_resurfacing, mrr, precision_at_k
from wanderlens.core.gallery import build_gallery
from wanderlens.core.recommend import (
    filter_unvisited_proximity,
    rank_destinations,
    taste_attribute_weights,
)
from wanderlens.db import connect, init_db
from wanderlens.pipeline.recommend import (
    DEFAULT_CANDIDATE_COUNTRIES,
    build_catalog_for,
    ensure_destination_embeddings,
    load_profile,
    load_taste_embedding,
    load_taste_facets,
)

EVAL_MIN_POPULATION = 10000


def _eval_catalog(config, holdout_country: str, providers=None) -> JsonCatalog:
    country_names = config.catalog_path / "countryInfo.txt"
    codes = list(DEFAULT_CANDIDATE_COUNTRIES)
    if holdout_country:
        code = country_code_for_name(country_names, holdout_country)
        if code and code not in codes:
            codes.append(code)
    return build_catalog_for(
        config,
        codes,
        f"destinations_eval_{holdout_country.lower() or 'default'}.json",
        providers=providers,
        limit=300,
        min_population=EVAL_MIN_POPULATION,
    )


def _attribute_weights_excluding(conn, user_id: int, exclude_trip_id: int, total_trips: int) -> dict:
    rows = conn.execute(
        "SELECT trip_id, subject FROM trip_subjects WHERE user_id = ?", (user_id,)
    ).fetchall()
    per_trip: dict[int, set[str]] = {}
    for row in rows:
        if row["trip_id"] == exclude_trip_id:
            continue
        per_trip.setdefault(row["trip_id"], set()).add(row["subject"])
    counts: Counter = Counter()
    for attributes in per_trip.values():
        for attribute in attributes:
            counts[attribute] += 1
    total = total_trips or 1
    return {attribute: count / total for attribute, count in counts.items()}


def _pick_holdout(conn, user_id: int, trips, holdout: Optional[str]):
    if holdout:
        matches = [
            trip
            for trip in trips
            if (trip["city"] or "").lower() == holdout.lower()
            or (trip["country"] or "").lower() == holdout.lower()
        ]
        return matches[0] if matches else None
    return max(
        trips,
        key=lambda trip: conn.execute(
            "SELECT COUNT(*) FROM trip_photos WHERE user_id = ? AND trip_id = ?",
            (user_id, trip["id"]),
        ).fetchone()[0],
    )


def run_eval(
    config,
    user_name: str = "owner",
    holdout: Optional[str] = None,
    within_top: int = 50,
    embedder=None,
    catalog: Optional[JsonCatalog] = None,
    providers=None,
) -> str:
    from wanderlens.pipeline.ingest import get_or_create_user

    conn = connect(config.db_path)
    init_db(conn)
    user_id = get_or_create_user(conn, user_name)

    trips = conn.execute(
        "SELECT id, city, country, lat, lon FROM trips WHERE user_id = ? ORDER BY id",
        (user_id,),
    ).fetchall()
    if not trips:
        return "No trips to hold out. Run ingestion and profiling first."

    hold = _pick_holdout(conn, user_id, trips, holdout)
    if hold is None:
        return f"'{holdout}' is not a visited trip; nothing to hold out."
    if hold["lat"] is None or hold["lon"] is None:
        return f"Held-out trip '{hold['city'] or hold['id']}' has no location."

    label = hold["city"] or hold["country"] or f"trip {hold['id']}"
    radius = getattr(config, "exclude_radius_km", 60.0)

    taste = load_taste_embedding(conn, user_id)
    facets = load_taste_facets(conn, user_id, exclude_trip_id=hold["id"])
    if not facets and taste is None:
        return "No photo embeddings found. Run ingestion first."

    if embedder is None:
        from wanderlens.models.embeddings import OnnxClipEmbedder

        embedder = OnnxClipEmbedder(cache_dir=config.data_dir / "models")

    catalog = catalog or _eval_catalog(config, hold["country"] or "", providers=providers)

    centers = [
        (trip["lat"], trip["lon"])
        for trip in trips
        if trip["id"] != hold["id"] and trip["lat"] is not None and trip["lon"] is not None
    ]
    candidates = filter_unvisited_proximity(catalog.candidates(), centers, radius)
    vectors = ensure_destination_embeddings(conn, candidates, embedder)

    other_trips = [trip for trip in trips if trip["id"] != hold["id"]]
    weights = _attribute_weights_excluding(conn, user_id, hold["id"], len(other_trips))
    profile = load_profile(conn, user_id, embedding=taste)

    ranked = rank_destinations(
        taste,
        candidates,
        embedder.embed_text,
        top_k=None,
        vectors=vectors,
        taste_tags=taste_attribute_weights(weights),
        taste_facets=facets,
    )
    result = evaluate_resurfacing(ranked, (hold["lat"], hold["lon"]), radius, within_top, label)
    return result.describe()


def run_synthetic_eval(k: int = 3, alpha: Optional[float] = None) -> str:
    """Rank the synthetic gallery and report precision@k / MRR.

    A reproducible quality signal that does not depend on the user's archive, so
    ranking changes can be compared without more real data.
    """
    gallery = build_gallery()
    ranked = rank_destinations(
        None,
        gallery.destinations,
        vectors=gallery.vectors,
        taste_tags=gallery.taste_tags,
        taste_facets=gallery.facets,
        alpha=0.25 if alpha is None else alpha,
        top_k=None,
    )
    ids = [rec.destination.id for rec in ranked]
    precision = precision_at_k(ids, gallery.relevant, k)
    reciprocal = mrr(ids, gallery.relevant)
    return f"Synthetic gallery (n={len(ids)}): precision@{k} = {precision:.2f}, MRR = {reciprocal:.2f}"
