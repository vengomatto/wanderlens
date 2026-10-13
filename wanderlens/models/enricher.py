from __future__ import annotations

import json

from wanderlens.core.models import Destination
from wanderlens.models.llm import HostedTextModel

_ATTR_SYSTEM = (
    "You turn a short list of travel photo tags into a JSON array of canonical "
    "travel attributes (subjects, activities, and visual character). Reply with "
    "ONLY a JSON array of lowercase short strings, no prose."
)

_DESC_SYSTEM = (
    "You write one rich, factual sentence describing a travel destination's "
    "character to improve text similarity matching. Use ONLY the given name, "
    "country, attributes, and description; do not invent facts. Plain text, no "
    "markdown, no preamble."
)


def _parse_list(raw: str) -> list[str]:
    start, end = raw.find("["), raw.rfind("]")
    if start < 0 or end <= start:
        return []
    try:
        parsed = json.loads(raw[start : end + 1])
    except ValueError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item).strip().lower() for item in parsed if str(item).strip()]


class HostedTasteEnricher:
    """Structured taste attribution and destination-text enrichment behind an
    injectable seam. The only place this file touches the hosted model."""

    name = "llm"
    prompt_version = "taste-enrich-v1"

    def __init__(self, api_key: str | None, model: str, timeout: int = 60):
        self.model = model
        self.text = HostedTextModel(api_key, model, timeout)

    def attribute_trip(self, tags, context: str = "") -> list[str]:
        payload = {"tags": list(tags), "context": context}
        raw = self.text.complete(_ATTR_SYSTEM + "\n\n" + json.dumps(payload, ensure_ascii=False))
        return _parse_list(raw)

    def description(self, destination: Destination) -> str:
        payload = {
            "name": destination.name,
            "country": destination.country,
            "attributes": list(destination.attributes),
            "description": destination.description,
        }
        return (self.text.complete(_DESC_SYSTEM + "\n\n" + json.dumps(payload, ensure_ascii=False)) or "").strip()
