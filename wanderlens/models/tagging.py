from __future__ import annotations

from typing import Sequence

import numpy as np

# A short phrase per canonical attribute; falls back to the attribute name.
PROMPTS: dict[str, str] = {
    "coastal": "a photo of the coast and the sea",
    "beach": "a photo of a sandy beach",
    "cliffs": "a photo of rocky cliffs",
    "water": "a photo of water",
    "boats": "a photo of boats in a harbour",
    "mountains": "a photo of mountains",
    "hiking": "a photo of a hiking trail",
    "snow": "a photo of snow",
    "lake": "a photo of a lake",
    "river": "a photo of a river or canal",
    "forest": "a photo of a forest",
    "wildlife": "a photo of wildlife or animals",
    "city": "a photo of a city skyline",
    "village": "a photo of a small village",
    "old_town": "a photo of an old town street",
    "architecture": "a photo of notable architecture",
    "food": "a photo of food or a restaurant",
    "museum": "a photo of a museum or gallery",
    "history": "a photo of ruins or historic monuments",
    "camping": "a photo of camping",
    "nature": "a photo of a nature landscape",
    "sunset": "a photo of a sunset",
    "desert": "a photo of a desert",
    "countryside": "a photo of countryside",
    "weather": "a photo of a dramatic sky",
}


class ZeroShotTagger:
    """Local zero-shot tagging: score CLIP image vectors against prompt vectors.

    Implements the ``VisionModel`` seam (``describe(paths) -> list[str]``) so the
    profile pipeline is unchanged. Distinct ``model``/``prompt_version`` keep its
    cache separate from the hosted vision model.
    """

    model = "clip-zero-shot"
    prompt_version = "zeroshot-v1"

    def __init__(self, embedder, top_k: int = 4, min_prob: float = 0.02):
        self.embedder = embedder
        self.top_k = top_k
        self.min_prob = min_prob
        self._labels = list(PROMPTS)
        text = [embedder.embed_text(PROMPTS[label]) for label in self._labels]
        self._text = np.stack([_unit(vector) for vector in text])

    def _probabilities(self, vector) -> np.ndarray:
        similarities = self._text @ _unit(vector)
        scaled = np.exp((similarities - similarities.max()) * 100.0)
        return scaled / scaled.sum()

    def describe(self, paths: Sequence[str]) -> list[str]:
        tags: list[str] = []
        for path in paths:
            try:
                vector = self.embedder.embed_image(path)
            except Exception:
                continue
            probs = self._probabilities(np.asarray(vector, dtype=np.float32))
            for index in np.argsort(-probs)[: self.top_k]:
                if probs[index] >= self.min_prob:
                    tags.append(self._labels[index])
        return tags


def _unit(vector) -> np.ndarray:
    vector = np.asarray(vector, dtype=np.float32)
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm else vector
