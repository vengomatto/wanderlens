from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np

DEFAULT_REPO_DIRNAME = "clip-vit-base-patch32"
_HF_BASE = "https://huggingface.co/Xenova/clip-vit-base-patch32/resolve/main"
MODEL_FILES = (
    "onnx/vision_model_quantized.onnx",
    "onnx/text_model_quantized.onnx",
    "tokenizer.json",
)

CLIP_MEAN = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
CLIP_STD = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)
IMAGE_SIZE = 224
CONTEXT_LENGTH = 77


def ensure_model(cache_dir: str | Path = "data/models") -> Path:
    """Download the CLIP ONNX + tokenizer once into ``cache_dir`` if missing."""
    import requests

    target = Path(cache_dir) / DEFAULT_REPO_DIRNAME
    for rel in MODEL_FILES:
        dest = target / rel
        if dest.exists() and dest.stat().st_size > 0:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        with requests.get(f"{_HF_BASE}/{rel}", stream=True, timeout=120) as resp:
            resp.raise_for_status()
            with open(tmp, "wb") as fh:
                for chunk in resp.iter_content(1 << 16):
                    fh.write(chunk)
        tmp.replace(dest)
    return target


class OnnxClipEmbedder:
    """Local CLIP embeddings via ONNX Runtime.

    The only module allowed to import the vision runtime; callers depend on the
    ``EmbeddingModel`` port. Sessions load lazily, so importing is cheap.
    """

    def __init__(self, model_dir: Optional[str | Path] = None, cache_dir: str | Path = "data/models"):
        self.model_dir = Path(model_dir) if model_dir else ensure_model(cache_dir)
        from tokenizers import Tokenizer

        self._tokenizer = Tokenizer.from_file(str(self.model_dir / "tokenizer.json"))
        self._tokenizer.no_padding()
        self._tokenizer.no_truncation()
        self._vision = None
        self._text = None

    @property
    def dim(self) -> int:
        return 512

    def _session(self, which: str):
        cached = self._vision if which == "vision" else self._text
        if cached is None:
            import onnxruntime as ort

            filename = f"{which}_model_quantized.onnx"
            cached = ort.InferenceSession(
                str(self.model_dir / "onnx" / filename),
                providers=["CPUExecutionProvider"],
            )
            if which == "vision":
                self._vision = cached
            else:
                self._text = cached
        return cached

    @staticmethod
    def _normalize(vector: np.ndarray) -> np.ndarray:
        vector = vector.astype(np.float32)
        norm = np.linalg.norm(vector)
        return vector / norm if norm else vector

    def _preprocess(self, path: str) -> np.ndarray:
        from PIL import Image

        with Image.open(path) as image:
            image = image.convert("RGB")
            width, height = image.size
            scale = IMAGE_SIZE / min(width, height)
            resized = image.resize((round(width * scale), round(height * scale)), Image.BICUBIC)
            left = (resized.width - IMAGE_SIZE) // 2
            top = (resized.height - IMAGE_SIZE) // 2
            cropped = resized.crop((left, top, left + IMAGE_SIZE, top + IMAGE_SIZE))
        array = np.asarray(cropped, dtype=np.float32) / 255.0
        array = (array - CLIP_MEAN) / CLIP_STD
        return array.transpose(2, 0, 1)[None, ...]

    def embed_image(self, path: str) -> np.ndarray:
        session = self._session("vision")
        pixels = self._preprocess(path)
        embeds = session.run(None, {"pixel_values": pixels})[0]
        return self._normalize(embeds[0])

    def _encode_text(self, text: str) -> np.ndarray:
        ids = self._tokenizer.encode(text).ids[:CONTEXT_LENGTH]
        ids = ids + [0] * (CONTEXT_LENGTH - len(ids))
        return np.array([ids], dtype=np.int64)

    def embed_text(self, text: str) -> np.ndarray:
        session = self._session("text")
        embeds = session.run(None, {"input_ids": self._encode_text(text)})[0]
        return self._normalize(embeds[0])
