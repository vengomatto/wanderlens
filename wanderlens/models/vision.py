from __future__ import annotations

import base64
import re
from io import BytesIO
from pathlib import Path
from typing import Sequence

import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_IMAGE_PX = 512


def prepare_image(path: str, max_px: int = MAX_IMAGE_PX) -> bytes:
    """A small, EXIF-stripped JPEG for the vision model (no GPS/time leak)."""
    from PIL import Image, ImageOps

    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail((max_px, max_px))
        buffer = BytesIO()
        image.save(buffer, "JPEG", quality=80)
    return buffer.getvalue()

_SYSTEM = (
    "You are a travel photo analyst. For the provided photos, respond with a "
    "single comma-separated list of short attribute tags describing subjects, "
    "activities, and visual character (for example: coastal cliffs, hiking, "
    "old town, seafood). Reply with tags only, no sentences."
)


class HostedVLM:
    """Vision model behind the ``VisionModel`` port.

    The only module allowed to make vision-LLM HTTP calls. Kept injectable so
    tests never touch the network.
    """

    def __init__(self, api_key: str | None, model: str, timeout: int = 60):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def _encode(self, path: str) -> str:
        return base64.b64encode(prepare_image(path)).decode("ascii")

    def describe(self, paths: Sequence[str]) -> list[str]:
        if not self.api_key:
            raise RuntimeError("no vision API key configured")
        content: list[dict] = [{"type": "text", "text": "Tag these travel photos."}]
        for path in paths:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{self._encode(path)}",
                        "detail": "low",
                    },
                }
            )
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": content},
                ],
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"]
        parts = re.split(r"[,;\n]", text)
        return [tag.strip().lower() for tag in parts if tag.strip()]
