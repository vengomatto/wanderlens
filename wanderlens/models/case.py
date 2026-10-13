from __future__ import annotations

import json

from wanderlens.core.models import Destination
from wanderlens.models.llm import HostedTextModel

_SYSTEM = (
    "You write a short, compelling case for visiting a travel destination "
    "(three to four sentences) that makes the reader want to go. Use ONLY the "
    "provided facts and search results; do not invent places, prices, or claims. "
    "Lead with what makes it special, then a concrete reason to go. "
    'Reply with JSON: {"narrative": "...", "sources": [{"title": "...", '
    '"url": "..."}]} using only URLs from the provided search results. No markdown.'
)


class HostedCaseWriter:
    """Writes a grounded destination case behind an injectable seam."""

    name = "llm"
    prompt_version = "case-v1"

    def __init__(self, api_key: str | None, model: str, timeout: int = 60):
        self.model = model
        self.text = HostedTextModel(api_key, model, timeout)

    def write(self, destination: Destination, facts: dict, search_results: list[dict]) -> dict:
        payload = {
            "destination": {
                "name": destination.name,
                "country": destination.country,
                "attributes": list(destination.attributes),
            },
            "facts": facts,
            "search_results": [
                {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("snippet", "")}
                for r in (search_results or [])
            ],
        }
        raw = self.text.complete(_SYSTEM + "\n\n" + json.dumps(payload, ensure_ascii=False))
        return _parse(raw)


def _parse(raw: str) -> dict:
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        parsed = json.loads(raw[start : end + 1])
    except ValueError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    narrative = str(parsed.get("narrative", "")).strip()
    sources: list[dict] = []
    for item in parsed.get("sources", []) or []:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url", "")).strip()
        if not url.startswith("http"):
            continue
        sources.append({"title": str(item.get("title", "")).strip(), "url": url})
    return {"narrative": narrative, "sources": sources}
