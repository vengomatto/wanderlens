from __future__ import annotations

import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class HostedTextModel:
    """A hosted chat model behind a tiny seam. The only module-family allowed to
    make LLM HTTP calls (alongside vision.py / ranker.py)."""

    def __init__(self, api_key: str | None, model: str, timeout: int = 60):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def complete(self, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("no LLM API key configured")
        response = requests.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"model": self.model, "messages": [{"role": "user", "content": prompt}]},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
