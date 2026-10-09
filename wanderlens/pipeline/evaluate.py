from __future__ import annotations

from typing import Optional

from wanderlens.catalog.destinations import JsonCatalog
from wanderlens.catalog.fetch import (
    build_catalog,
    country_code_for_name,
    enrich_records,
    load_geonames_cities,
)
from wanderlens.core.evaluate import evaluate_holdout
from wanderlens.core.recommend import rank_destinations, taste_attribute_weights
from wanderlens.db import connect, init_db
from wanderlens.pipeline.recommend import (
    DEFAULT_CANDIDATE_COUNTRIES,
    ensure_destination_embeddings,
    load_profile,
    load_taste_embedding,
)

EVAL_MIN_POPULATION = 10000


def _eval_catalog(config, holdout: str, providers=None) -> JsonCatalog:
    cache = config.catalog_path / f"destinations_eval_{holdout.lower()}.json"
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
    holdout_code = country_code_for_name(country_names, holdout) if country_names.exists() else None
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

    visited = [
        row["key"]
        for row in conn.execute(
            "SELECT key FROM profile_entries WHERE user_id = ? AND factor = 'geography'",
            (user_id,),
        )
    ]
    if not visited:
        return "No visited geography to hold out. Run ingestion and profiling first."

    holdout = holdout or sorted(visited)[0]
    if holdout not in visited:
        return f"'{holdout}' is not a visited place in the profile; nothing to hold out."
    remaining = [country for country in visited if country != holdout]

    taste = load_taste_embedding(conn, user_id)
    if taste is None:
        return "No photo embeddings found. Run ingestion first."

    if embedder is None:
        from wanderlens.models.embeddings import OnnxClipEmbedder

        embedder = OnnxClipEmbedder(cache_dir=config.data_dir / "models")

    catalog = catalog or _eval_catalog(config, holdout, providers=providers)
    candidates = catalog.candidates()
    vectors = ensure_destination_embeddings(conn, candidates, embedder)
    profile = load_profile(conn, user_id, embedding=taste)
    ranked = rank_destinations(
        taste,
        candidates,
        embedder.embed_text,
        exclude_countries=remaining,
        top_k=None,
        vectors=vectors,
        taste_tags=taste_attribute_weights(profile.tags),
    )
    result = evaluate_holdout(ranked, holdout, within_top)
    return result.describe()
