from __future__ import annotations

from typing import Optional

from wanderlens.catalog.fetch import fetch_wikidata_description, fetch_wikipedia_summary


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


def build_provider_chain(config) -> list:
    """Build the ordered Description Provider chain from configuration."""
    from wanderlens.models.llm import HostedTextModel

    chain: list = []
    for key in getattr(config, "description_providers", ["wikimedia", "llm"]):
        if key == "wikimedia":
            chain.append(WikimediaProvider())
        elif key == "llm":
            chain.append(
                LlmProvider(
                    HostedTextModel(
                        config.api_key,
                        getattr(config, "llm_model", "openai/gpt-4o-mini:online"),
                    )
                )
            )
    return chain
