from __future__ import annotations

import json

from wanderlens.core.models import Destination
from wanderlens.models.llm import HostedTextModel

_SYSTEM = (
    "You produce a structured travel-destination profile as JSON with keys: "
    '"vibe" (object mapping short lowercase attribute words to a number 0..1), '
    '"typical_stay_days" (positive integer), "family_suitability", "walkability", '
    '"base_camp" (each one of "low"|"medium"|"high"), and "summary" (one short '
    "sentence). Use ONLY the given facts; no markdown, no prose outside the JSON."
)

_SUITABILITY = {"low", "medium", "high"}


class HostedProfileWriter:
    """Builds a structured Destination profile behind an injectable seam."""

    name = "llm"
    prompt_version = "profile-v1"

    def __init__(self, api_key: str | None, model: str, timeout: int = 60):
        self.model = model
        self.text = HostedTextModel(api_key, model, timeout)

    def write(self, destination: Destination, facts: dict) -> dict:
        payload = {
            "destination": {
                "name": destination.name,
                "country": destination.country,
                "granularity": destination.granularity,
                "attributes": list(destination.attributes),
            },
            "facts": facts,
        }
        raw = self.text.complete(_SYSTEM + "\n\n" + json.dumps(payload, ensure_ascii=False))
        return parse_profile(raw)


def parse_profile(raw: str) -> dict:
    """Validate and clean a model's profile JSON; anything invalid is dropped."""
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        data = json.loads(raw[start : end + 1])
    except ValueError:
        return {}
    if not isinstance(data, dict):
        return {}

    out: dict = {}
    vibe = data.get("vibe")
    if isinstance(vibe, dict):
        clean: dict[str, float] = {}
        for key, value in vibe.items():
            if isinstance(value, (int, float)) and 0.0 <= float(value) <= 1.0:
                clean[str(key).strip().lower()] = round(float(value), 3)
        if clean:
            out["vibe"] = clean
    stay = data.get("typical_stay_days")
    if isinstance(stay, int) and stay > 0:
        out["typical_stay_days"] = stay
    for key in ("family_suitability", "walkability", "base_camp"):
        value = data.get(key)
        if isinstance(value, str) and value.strip().lower() in _SUITABILITY:
            out[key] = value.strip().lower()
    summary = data.get("summary")
    if isinstance(summary, str) and summary.strip():
        out["summary"] = summary.strip()[:400]
    return out
