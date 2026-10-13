from __future__ import annotations

import time
from typing import Optional

from wanderlens.catalog.fetch import fetch_wikidata_description, fetch_wikipedia_summary

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSM_USER_AGENT = "wanderlens/0.1 (+https://github.com/Vengomatto/wanderlens)"

_FEATURE_WORDS = {
    "natural": {
        "coastline": "coastal",
        "water": "water",
        "beach": "beach",
        "bay": "bay",
        "peak": "mountains",
        "wood": "forest",
        "wetland": "nature",
    },
    "leisure": {
        "beach_resort": "beach",
        "marina": "marina",
        "park": "nature",
        "nature_reserve": "nature",
        "garden": "nature",
    },
    "tourism": {"attraction": "nature", "viewpoint": "viewpoint", "museum": "museum"},
    "historic": {
        "castle": "history",
        "fort": "history",
        "monument": "history",
        "ruins": "history",
        "archaeological_site": "history",
    },
    "landuse": {"forest": "forest", "vineyard": "countryside", "orchard": "countryside"},
    "harbour": {"yes": "marina"},
}


class WikimediaProvider:
    """Wikipedia intro extract, falling back to the Wikidata short description."""

    name = "wikimedia"

    def __init__(self, session=None):
        self.session = session

    def describe(self, name: str, country: str) -> Optional[str]:
        try:
            summary = fetch_wikipedia_summary(name, country, session=self.session)
            if summary:
                return summary
        except Exception:
            pass
        try:
            return fetch_wikidata_description(name, session=self.session) or None
        except Exception:
            return None


class LlmProvider:
    """One factual sentence from a hosted (optionally search-grounded) LLM."""

    name = "llm"

    def __init__(self, text_model):
        self.text_model = text_model

    def describe(self, name: str, country: str) -> Optional[str]:
        prompt = (
            f"In one factual sentence, describe {name}, {country} as a travel "
            f"destination: its landscape, setting, and character."
        )
        try:
            text = self.text_model.complete(prompt)
        except Exception:
            return None
        text = (text or "").strip()
        return text or None


class OsmProvider:
    """Free, keyless feature text from OpenStreetMap.

    Resolves the place via Nominatim, then tallies nearby OSM features via
    Overpass. Best-effort: any failure returns ``None`` so the chain continues.
    """

    name = "openstreetmap"
    endpoints = (
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    )

    def __init__(self, session=None, delay: float = 1.0, timeout: int = 45, radius: int = 3000):
        self.session = session
        self.delay = delay
        self.timeout = timeout
        self.radius = radius

    def describe(self, name: str, country: str) -> Optional[str]:
        import requests

        self._http = self.session or requests
        coordinates = self._geocode(name, country)
        if not coordinates:
            return None
        counts = self._nearby_features(*coordinates)
        words = {
            _FEATURE_WORDS[key][value]
            for key, value in counts
            if key in _FEATURE_WORDS and value in _FEATURE_WORDS[key]
        }
        if not words:
            return None
        return "OpenStreetMap features: " + ", ".join(sorted(words)) + "."

    def _geocode(self, name: str, country: str) -> Optional[tuple[float, float]]:
        if self.delay:
            time.sleep(self.delay)
        try:
            response = self._http.get(
                NOMINATIM_URL,
                params={"q": f"{name}, {country}".strip(", "), "format": "json", "limit": 1},
                headers={"User-Agent": OSM_USER_AGENT},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return float(data[0]["lat"]), float(data[0]["lon"])
        except Exception:
            return None

    def _nearby_features(self, lat: float, lon: float) -> set[tuple[str, str]]:
        query = (
            f"[out:json][timeout:{max(10, self.timeout - 10)}];("
            f'nwr(around:{self.radius},{lat},{lon})["natural"];'
            f'nwr(around:{self.radius},{lat},{lon})["leisure"];'
            f'nwr(around:{self.radius},{lat},{lon})["historic"];'
            f'nwr(around:{self.radius},{lat},{lon})["harbour"];'
            ");out tags;"
        )
        payload = None
        for endpoint in self.endpoints:
            try:
                response = self._http.post(
                    endpoint,
                    data={"data": query},
                    headers={"User-Agent": OSM_USER_AGENT},
                    timeout=self.timeout,
                )
                if response.status_code == 200:
                    payload = response.json()
                    break
            except Exception:
                continue
        if not payload:
            return set()
        features: set[tuple[str, str]] = set()
        for element in payload.get("elements", []):
            tags = element.get("tags", {})
            for key in ("natural", "leisure", "historic", "harbour"):
                if key in tags:
                    features.add((key, tags[key]))
        return features


def build_provider_chain(config) -> list:
    """Build the ordered Description Provider chain from configuration."""
    from wanderlens.models.llm import HostedTextModel

    chain: list = []
    for key in getattr(config, "description_providers", ["wikimedia", "openstreetmap", "llm"]):
        if key == "wikimedia":
            chain.append(WikimediaProvider())
        elif key == "openstreetmap":
            chain.append(OsmProvider())
        elif key == "llm":
            chain.append(
                LlmProvider(
                    HostedTextModel(
                        config.api_key,
                        getattr(config, "llm_model", "meta-llama/llama-3.1-8b-instruct"),
                    )
                )
            )
    return chain
