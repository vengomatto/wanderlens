import ast
from pathlib import Path

import pytest
from PIL import Image

from wanderlens.models.embeddings import CONTEXT_LENGTH, OnnxClipEmbedder

REPO = Path(__file__).resolve().parent.parent
MODEL_DIR = REPO / "data" / "models" / "clip-vit-base-patch32"

HEAVY = {"onnxruntime", "tokenizers", "torch", "open_clip"}


def test_dim_is_512():
    embedder = OnnxClipEmbedder.__new__(OnnxClipEmbedder)
    assert embedder.dim == 512


def test_heavy_runtime_confined_to_models_package():
    for path in (REPO / "wanderlens").rglob("*.py"):
        if path.parts[-2] == "models" or path.parent.name == "models":
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in HEAVY, f"{path} imports {alias.name}"
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in HEAVY, f"{path} imports {node.module}"


@pytest.mark.skipif(not MODEL_DIR.exists(), reason="CLIP ONNX model not downloaded")
def test_real_embedder_produces_unit_vector(tmp_path):
    photo = tmp_path / "p.jpg"
    Image.new("RGB", (640, 480), (30, 90, 160)).save(photo)

    embedder = OnnxClipEmbedder()
    vector = embedder.embed_image(str(photo))

    assert vector.shape == (512,)
    assert abs(float((vector ** 2).sum()) ** 0.5 - 1.0) < 1e-3
    assert len(embedder._encode_text("hello world")[0]) == CONTEXT_LENGTH
