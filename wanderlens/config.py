from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional

import yaml


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

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)


def _pick(*candidates: Optional[str]) -> Optional[str]:
    for c in candidates:
        if c:
            return c
    return None


def load_config(
    config_path: Optional[str | Path] = None,
    env: Optional[Mapping[str, str]] = None,
) -> Config:
    env = dict(os.environ if env is None else env)

    values: dict = {}
    if config_path and Path(config_path).exists():
        loaded = yaml.safe_load(Path(config_path).read_text()) or {}
        if not isinstance(loaded, dict):
            raise ValueError(f"config {config_path} must be a mapping")
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
    )
