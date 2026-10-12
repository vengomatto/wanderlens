from __future__ import annotations

import json

import requests

from wanderlens.models.llm import HostedTextModel

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

_EXPLAIN_PROMPT_VERSION = "explain-v1"

_EXPLAIN_SYSTEM = (
    "You write a short, specific explanation (two sentences max) of why a travel "
    "destination matches a user's taste. Use ONLY the provided facts; do not "
    "invent places, attributes, or trips. Mention the closest visited trip and "
    "the shared attributes. Plain text, no markdown, no preamble."
)

_SYSTEM = (
    "You re-rank travel destination suggestions for a user and explain each. "
    "Reply with JSON: a list of objects with keys 'id' (the destination id) and "
    "'explanation' (one sentence grounded in the user's photo-derived taste). "
    "Return every id you were given."
)


class HostedRanker:
    """LLM re-ranker behind an injectable seam; tests use a deterministic stub."""

    def __init__(self, api_key: str | None, model: str, timeout: int = 60):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def rank(self, recommendations, profile):
        if not self.api_key:
            raise RuntimeError("no API key configured")
        shortlist = [
            {"id": r.destination.id, "name": r.destination.name, "country": r.destination.country}
            for r in recommendations
        ]
        payload = {
            "taste": {"visited": list(profile.geography), "subjects": list(profile.tags)},
            "candidates": shortlist,
        }
        response = requests.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": json.dumps(payload)},
                ],
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(text[text.find("[") : text.rfind("]") + 1])
        by_id = {item["id"]: item.get("explanation", "") for item in parsed}
        order = {item["id"]: i for i, item in enumerate(parsed)}
        ordered = sorted(recommendations, key=lambda r: order.get(r.destination.id, len(order)))
        for rank, rec in enumerate(ordered, start=1):
            rec.rank = rank
            rec.explanation = by_id.get(rec.destination.id, "")
        return ordered


class HostedExplanationSynthesizer:
    """Rewrites a Recommendation's evidence into prose. Pinned model + prompt."""

    name = "llm"
    prompt_version = _EXPLAIN_PROMPT_VERSION

    def __init__(self, api_key: str | None, model: str, timeout: int = 60):
        self.model = model
        self.text = HostedTextModel(api_key, model, timeout)

    def synthesize(self, evidence: dict) -> str:
        prompt = _EXPLAIN_SYSTEM + "\n\nFacts:\n" + json.dumps(evidence, ensure_ascii=False)
        return (self.text.complete(prompt) or "").strip()
