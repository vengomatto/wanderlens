from __future__ import annotations

from typing import Optional

from wanderlens.catalog.destinations import JsonCatalog
from wanderlens.catalog.fetch import build_catalog, enrich_records, load_geonames_cities
from wanderlens.core.evaluate import evaluate_holdout
from wanderlens.core.recommend import rank_destinations
from wanderlens.db import connect, init_db
from wanderlens.pipeline.recommend import (
    DEFAULT_CANDIDATE_COUNTRIES,
    load_taste_embedding,
)

EVAL_MIN_POPULATION = 10000


def _eval_catalog(config, holdout: str, description_fetcher=None) -> JsonCatalog:
    countries = list(dict.fromkeys(DEFAULT_CANDIDATE_COUNTRIES + [holdout]))
    cities = config.catalog_path / "cities500.txt"
    if not cities.exists():
        return JsonCatalog([])
    country_names = config.catalog_path / "countryInfo.txt"
    countries_path = country_names if country_names.exists() else None
    others = [c for c in countries if c != holdout]
    records = load_geonames_cities(
        cities,
        country_codes=others,
        min_population=EVAL_MIN_POPULATION,
        limit=300,
        countries_path=countries_path,
    )
    records += load_geonames_cities(
        cities,
        country_codes=[holdout],
        min_population=EVAL_MIN_POPULATION,
        countries_path=countries_path,
    )
    enrich_records(records, fetch=description_fetcher)
    return build_catalog({"geonames": records})


def run_eval(
    config,
    user_name: str = "owner",
    holdout: Optional[str] = None,
    within_top: int = 50,
    embedder=None,
    catalog: Optional[JsonCatalog] = None,
    description_fetcher=None,
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

    catalog = catalog or _eval_catalog(config, holdout, description_fetcher=description_fetcher)
    ranked = rank_destinations(
        taste,
        catalog.candidates(),
        embedder.embed_text,
        exclude_countries=remaining,
        top_k=None,
    )
    result = evaluate_holdout(ranked, holdout, within_top)
    return result.describe()
