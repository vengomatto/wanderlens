from __future__ import annotations

import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from wanderlens.core.models import Destination

DEFAULT_IMAGE_LIMIT = 4


def fetch_destination_image_urls(destination: Destination, session=None, limit: int = 4) -> list[str]:
    """Hero image URLs for a Destination, via the Wikimedia media provider."""
    from wanderlens.catalog.media import WikimediaMediaProvider

    try:
        bundle = WikimediaMediaProvider(session=session).fetch(destination)
    except Exception:
        return []
    if bundle is None:
        return []
    return [image.url for image in bundle.images if image.url][:limit]


def _download(session, url: str) -> bytes:
    import requests

    from wanderlens.catalog.fetch import USER_AGENT

    response = (session or requests).get(
        url, headers={"User-Agent": USER_AGENT}, timeout=60
    )
    response.raise_for_status()
    return response.content


def _unit(vector) -> np.ndarray:
    vector = np.asarray(vector, dtype=np.float32)
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm else vector


def ensure_destination_image_embeddings(
    conn: sqlite3.Connection,
    destinations,
    embedder,
    fetch_urls=None,
    session=None,
    limit: int = DEFAULT_IMAGE_LIMIT,
) -> dict:
    """Return {destination_id: image vector}, fetching, embedding, and caching."""
    fetch_urls = fetch_urls or fetch_destination_image_urls
    base = getattr(embedder, "cache_key", None) or getattr(embedder, "name", "default")
    model = f"image:{base}"

    cached = {
        row["destination_id"]: np.frombuffer(row["vector"], dtype=np.float32)
        for row in conn.execute(
            "SELECT destination_id, vector FROM destination_image_embeddings WHERE model = ?",
            (model,),
        )
    }
    result = dict(cached)

    for destination in destinations:
        if destination.id in result:
            continue
        try:
            urls = fetch_urls(destination, session=session, limit=limit) or []
        except Exception:
            urls = []
        vectors: list[np.ndarray] = []
        for url in urls[:limit]:
            tmp = None
            try:
                data = _download(session, url)
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as handle:
                    handle.write(data)
                    tmp = handle.name
                vectors.append(embedder.embed_image(tmp))
            except Exception:
                continue
            finally:
                if tmp:
                    Path(tmp).unlink(missing_ok=True)
        if not vectors:
            continue
        mean = _unit(np.mean(np.stack([_unit(v) for v in vectors]), axis=0)).astype(np.float32)
        result[destination.id] = mean
        conn.execute(
            "INSERT OR REPLACE INTO destination_image_embeddings "
            "(destination_id, model, dim, vector, count, fetched_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                destination.id,
                model,
                int(mean.shape[0]),
                mean.tobytes(),
                len(vectors),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    return result
