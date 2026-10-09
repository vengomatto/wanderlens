from __future__ import annotations

from collections import Counter
from typing import Optional

from wanderlens.catalog.destinations import JsonCatalog
from wanderlens.catalog.fetch import (
    build_catalog,
    country_code_for_name,
    enrich_records,
    load_geonames_cities,
)
from wanderlens.core.evaluate import evaluate_resurfacing
from wanderlens.core.recommend import (
    filter_unvisited_proximity,
    rank_destinations,
    taste_attribute_weights,
)
from wanderlens.db import connect, init_db
from wanderlens.pipeline.recommend import (
    DEFAULT_CANDIDATE_COUNTRIES,
    ensure_destination_embeddings,
    load_profile,
    load_taste_embedding,
    load_taste_facets,
)

EVAL_MIN_POPULATION = 10000


def _eval_catalog(config, holdout_country: str, providers=None) -> JsonCatalog:
    cache = config.catalog_path / f"destinations_eval_{holdout_country.lower()}.json"
    if cache.exists():
        return JsonCatalog.load(cache)

    cities = config.catalog_path / "cities500.txt"
    if not cities.exists():
        return JsonCatalog([])
    country_names = config.catalog_path / "countryInfo.txt"
    countries_path = country_names if country_names.exists() else None

    records = load_geonames_cities(
        cities,
        country_codes=DEFAULT_CANDIDATE_COUNTRIES,
        min_population=EVAL_MIN_POPULATION,
        limit=300,
        countries_path=countries_path,
    )
    holdout_code = (
        country_code_for_name(country_names, holdout_country)
        if country_names.exists() and holdout_country
        else None
    )
    records += load_geonames_cities(
        cities,
        country_codes=[holdout_code] if holdout_code else None,
        min_population=EVAL_MIN_POPULATION,
        countries_path=countries_path,
    )
    if providers is None:
        from wanderlens.catalog.providers import build_provider_chain

        providers = build_provider_chain(config)
    enrich_records(records, providers=providers)
    catalog = build_catalog({"geonames": records})
    catalog.save(cache)
    return catalog


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
