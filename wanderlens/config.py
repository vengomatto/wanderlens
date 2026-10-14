from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional

import yaml

DEFAULT_TRAVEL_BLOGS = [
    "https://www.nomadicmatt.com/travel-guides/",
    "https://www.lonelyplanet.com/",
]


@dataclass
class Config:
    data_dir: Path
    photos_dir: Path
    db_path: Path
    catalog_path: Path
    vlm_provider: str
    vlm_model: str
    api_key: Optional[str]
    description_providers: list[str] = field(
        default_factory=lambda: ["wikimedia", "openstreetmap", "llm"]
    )
    llm_model: str = "meta-llama/llama-3.1-8b-instruct"
    exclude_radius_km: float = 60.0
    catalog_source: str = "wikivoyage"
    tile_url: str = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    tile_attribution: str = "&copy; OpenStreetMap contributors"
    explain_llm: bool = False
    split_gap_hours: float = 18.0
    split_jump_km: float = 150.0
    facet_min_photos: int = 4
    alpha: float = 0.25
    enrich_taste: bool = True
    build_case: bool = True
    travel_blogs: list[str] = field(default_factory=lambda: list(DEFAULT_TRAVEL_BLOGS))
    media_sources: list[str] = field(default_factory=lambda: ["openverse"])
    refresh_media: bool = False
    embedder: str = "clip"
    unsplash_key: Optional[str] = None
    pexels_key: Optional[str] = None
    climate: bool = False
    climate_weight: float = 0.0
    season: str = ""
    tag_provider: str = "clip"
    image_matching: bool = False
    calibrate: bool = False
    catalog_countries: list[str] = field(default_factory=list)
    catalog_min_extract: int = 0
    build_profiles: bool = False
    taste_bias_weight: float = 0.0
    recency_half_life_days: float = 0.0
    anti_match_weight: float = 0.0
    candidate_prefilter: int = 20

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)


def _pick(*candidates: Optional[str]) -> Optional[str]:
    for c in candidates:
        if c:
            return c
    return None


def _resolve_config_path(config_path: Optional[str | Path], env: Mapping[str, str]):
    """Find the config file to load: explicit, env, or a discovered default."""
    if config_path:
        return Path(config_path)
    from_env = env.get("WANDERLENS_CONFIG")
    if from_env:
        return Path(from_env).expanduser()
    for candidate in (
        Path("config.yaml"),
        Path("config.yml"),
        Path("data") / "config.yaml",
        Path.home() / ".config" / "wanderlens" / "config.yaml",
    ):
        if candidate.exists():
            return candidate
    return None


def load_config(
    config_path: Optional[str | Path] = None,
    env: Optional[Mapping[str, str]] = None,
) -> Config:
    env = dict(os.environ if env is None else env)

    values: dict = {}
    resolved = _resolve_config_path(config_path, env)
    if resolved and Path(resolved).exists():
        loaded = yaml.safe_load(Path(resolved).read_text()) or {}
        if not isinstance(loaded, dict):
            raise ValueError(f"config {resolved} must be a mapping")
        values = loaded

    data_dir = Path(values.get("data_dir") or env.get("WANDERLENS_DATA_DIR") or "data").expanduser()
    photos_dir = Path(
        values.get("photos_dir") or env.get("WANDERLENS_PHOTOS_DIR") or (data_dir / "photos")
    ).expanduser()
    db_path = Path(
        values.get("db_path") or env.get("WANDERLENS_DB") or (data_dir / "wanderlens.sqlite3")
    ).expanduser()
    catalog_path = Path(
        values.get("catalog_path") or env.get("WANDERLENS_CATALOG") or (data_dir / "catalog")
    ).expanduser()

    api_key = _pick(
        values.get("api_key"),
        values.get("openrouter_api_key"),
        env.get("WANDERLENS_VLM_API_KEY"),
        env.get("OPENROUTER_API_KEY"),
        env.get("ANTHROPIC_API_KEY"),
    )

    providers_raw = (
        values.get("description_providers")
        or env.get("WANDERLENS_DESCRIPTION_PROVIDERS")
        or ["wikimedia", "openstreetmap", "llm"]
    )
    if isinstance(providers_raw, str):
        description_providers = [p.strip() for p in providers_raw.split(",") if p.strip()]
    else:
        description_providers = list(providers_raw)

    return Config(
        data_dir=data_dir,
        photos_dir=photos_dir,
        db_path=db_path,
        catalog_path=catalog_path,
        vlm_provider=values.get("vlm_provider") or env.get("WANDERLENS_VLM_PROVIDER") or "openrouter",
        vlm_model=values.get("vlm_model")
        or env.get("WANDERLENS_VLM_MODEL")
        or "openai/gpt-4o-mini",
        api_key=api_key,
        description_providers=description_providers,
        llm_model=values.get("llm_model")
        or env.get("WANDERLENS_LLM_MODEL")
        or "meta-llama/llama-3.1-8b-instruct",
        exclude_radius_km=float(
            values.get("exclude_radius_km") or env.get("WANDERLENS_EXCLUDE_RADIUS_KM") or 60.0
        ),
        catalog_source=values.get("catalog_source")
        or env.get("WANDERLENS_CATALOG_SOURCE")
        or "wikivoyage",
        tile_url=values.get("tile_url")
        or env.get("WANDERLENS_TILE_URL")
        or "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        tile_attribution=values.get("tile_attribution")
        or env.get("WANDERLENS_TILE_ATTRIBUTION")
        or "&copy; OpenStreetMap contributors",
        explain_llm=bool(values.get("explain_llm"))
        or str(env.get("WANDERLENS_EXPLAIN_LLM", "")).lower() in {"1", "true", "yes", "on"},
        split_gap_hours=float(
            values.get("split_gap_hours") or env.get("WANDERLENS_SPLIT_GAP_HOURS") or 18.0
        ),
        split_jump_km=float(
            values.get("split_jump_km") or env.get("WANDERLENS_SPLIT_JUMP_KM") or 150.0
        ),
        facet_min_photos=int(
            values.get("facet_min_photos") or env.get("WANDERLENS_FACET_MIN_PHOTOS") or 4
        ),
        alpha=float(values.get("alpha") or env.get("WANDERLENS_ALPHA") or 0.25),
        enrich_taste=(
            bool(values.get("enrich_taste"))
            if "enrich_taste" in values
            else str(env.get("WANDERLENS_ENRICH_TASTE", "1")).lower() in {"1", "true", "yes", "on"}
        ),
        travel_blogs=_string_list(
            values.get("travel_blogs") or env.get("WANDERLENS_TRAVEL_BLOGS")
        )
        or list(DEFAULT_TRAVEL_BLOGS),
        build_case=(
            bool(values.get("build_case"))
            if "build_case" in values
            else str(env.get("WANDERLENS_BUILD_CASE", "1")).lower() in {"1", "true", "yes", "on"}
        ),
        media_sources=_string_list(
            values.get("media_sources") or env.get("WANDERLENS_MEDIA_SOURCES")
        )
        or ["openverse"],
        refresh_media=(
            bool(values.get("refresh_media"))
            if "refresh_media" in values
            else str(env.get("WANDERLENS_REFRESH_MEDIA", "")).lower() in {"1", "true", "yes", "on"}
        ),
        embedder=values.get("embedder") or env.get("WANDERLENS_EMBEDDER") or "clip",
        unsplash_key=_pick(values.get("unsplash_key"), env.get("WANDERLENS_UNSPLASH_KEY")),
        pexels_key=_pick(values.get("pexels_key"), env.get("WANDERLENS_PEXELS_KEY")),
        climate=(
            bool(values.get("climate"))
            if "climate" in values
            else str(env.get("WANDERLENS_CLIMATE", "")).lower() in {"1", "true", "yes", "on"}
        ),
        climate_weight=float(
            values.get("climate_weight") or env.get("WANDERLENS_CLIMATE_WEIGHT") or 0.0
        ),
        season=str(values.get("season") or env.get("WANDERLENS_SEASON") or "").lower(),
        tag_provider=str(
            values.get("tag_provider") or env.get("WANDERLENS_TAG_PROVIDER") or "clip"
        ).lower(),
        image_matching=(
            bool(values.get("image_matching"))
            if "image_matching" in values
            else str(env.get("WANDERLENS_IMAGE_MATCHING", "")).lower() in {"1", "true", "yes", "on"}
        ),
        calibrate=(
            bool(values.get("calibrate"))
            if "calibrate" in values
            else str(env.get("WANDERLENS_CALIBRATE", "")).lower() in {"1", "true", "yes", "on"}
        ),
        catalog_countries=_string_list(
            values.get("catalog_countries") or env.get("WANDERLENS_CATALOG_COUNTRIES")
        ),
        catalog_min_extract=int(
            values.get("catalog_min_extract") or env.get("WANDERLENS_CATALOG_MIN_EXTRACT") or 0
        ),
        build_profiles=(
            bool(values.get("build_profiles"))
            if "build_profiles" in values
            else str(env.get("WANDERLENS_BUILD_PROFILES", "")).lower() in {"1", "true", "yes", "on"}
        ),
        taste_bias_weight=float(
            values.get("taste_bias_weight") or env.get("WANDERLENS_TASTE_BIAS_WEIGHT") or 0.0
        ),
        recency_half_life_days=float(
            values.get("recency_half_life_days")
            or env.get("WANDERLENS_RECENCY_HALF_LIFE_DAYS")
            or 0.0
        ),
        anti_match_weight=float(
            values.get("anti_match_weight") or env.get("WANDERLENS_ANTI_MATCH_WEIGHT") or 0.0
        ),
        candidate_prefilter=int(
            values.get("candidate_prefilter") or env.get("WANDERLENS_CANDIDATE_PREFILTER") or 20
        ),
    )


def _string_list(raw) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, str):
        return [item.strip() for item in raw.split(",") if item.strip()]
    return [str(item).strip() for item in raw if str(item).strip()]
