from __future__ import annotations

import json
from typing import Optional

from wanderlens.core.models import Destination

NOMINATIM_SEARCH = "https://nominatim.openstreetmap.org/search"
NOMINATIM_LOOKUP = "https://nominatim.openstreetmap.org/lookup"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
OSM_USER_AGENT = "wanderlens/0.1 (+https://github.com/Vengomatto/wanderlens)"

CIRCLE_RADIUS_KM = {
    "region": 40.0,
    "other destination": 20.0,
    "city": 10.0,
}
DEFAULT_RADIUS_KM = 20.0
MAX_POINTS = 400


def resolve_region(
    destination: Destination, session=None, timeout: int = 30
) -> tuple[str, str, Optional[float]]:
    """Return ``(geojson, kind, radius_km)`` for a destination's area.

    ``kind`` is ``"precise"`` for a boundary polygon and ``"approximate"`` for a
    sized circle. With no coordinates, returns ``("", "", None)``.
    """
    if destination.lat is None or destination.lon is None:
        return "", "", None

    geometry = _precise_geometry(destination, session, timeout)
    if geometry:
        return json.dumps(_feature(geometry)), "precise", None

    radius = CIRCLE_RADIUS_KM.get(destination.granularity, DEFAULT_RADIUS_KM)
    point = {"type": "Point", "coordinates": [destination.lon, destination.lat]}
    return json.dumps(_feature(point)), "approximate", radius


def point_count(geometry: dict) -> int:
    def rings(polygon):
        return sum(len(ring) for ring in polygon)

    kind = geometry.get("type")
    if kind == "Polygon":
        return rings(geometry.get("coordinates", []))
    if kind == "MultiPolygon":
        return sum(rings(p) for p in geometry.get("coordinates", []))
    return 0


def _feature(geometry: dict) -> dict:
    return {"type": "Feature", "properties": {}, "geometry": geometry}


def _precise_geometry(destination: Destination, session, timeout: int) -> Optional[dict]:
    for geometry in (
        _wikidata_geometry(destination, session, timeout),
        _nominatim_geometry(destination, session, timeout),
    ):
        if geometry:
            return _simplify(geometry)
    return None


def _wikidata_geometry(destination: Destination, session, timeout: int) -> Optional[dict]:
    qid = destination.wikidata_id or (
        destination.id[3:] if destination.id.startswith("wd:") else ""
    )
    if not qid:
        return None
    import requests

    session = session or requests
    try:
        response = session.get(
            WIKIDATA_API,
            params={"action": "wbgetentities", "ids": qid, "props": "claims", "format": "json"},
            headers={"User-Agent": OSM_USER_AGENT},
            timeout=timeout,
        )
        response.raise_for_status()
        claims = response.json()["entities"][qid]["claims"]
        relation = claims["P402"][0]["mainsnak"]["datavalue"]["value"]
    except Exception:
        return None
    return _nominatim_lookup(f"R{relation}", session, timeout)


def _nominatim_geometry(destination: Destination, session, timeout: int) -> Optional[dict]:
    import requests

    session = session or requests
    query = f"{destination.name}, {destination.country}".strip(", ")
    try:
        response = session.get(
            NOMINATIM_SEARCH,
            params={"q": query, "format": "json", "limit": 1, "polygon_geojson": 1},
            headers={"User-Agent": OSM_USER_AGENT},
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
    except Exception:
        return None
    if not data:
        return None
    return data[0].get("geojson") or None


def _nominatim_lookup(osm_id: str, session, timeout: int) -> Optional[dict]:
    import requests

    session = session or requests
    try:
        response = session.get(
            NOMINATIM_LOOKUP,
            params={"osm_ids": osm_id, "format": "json", "polygon_geojson": 1},
            headers={"User-Agent": OSM_USER_AGENT},
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
    except Exception:
        return None
    if not data:
        return None
    return data[0].get("geojson") or None


def _simplify(geometry: dict) -> dict:
    kind = geometry.get("type")
    if kind == "Polygon":
        return {"type": "Polygon", "coordinates": _simplify_polygon(geometry.get("coordinates", []))}
    if kind == "MultiPolygon":
        return {
            "type": "MultiPolygon",
            "coordinates": [_simplify_polygon(p) for p in geometry.get("coordinates", [])],
        }
    return geometry


def _simplify_polygon(polygon: list) -> list:
    rings = [ring for ring in polygon if len(ring) >= 2]
    total = sum(len(ring) for ring in rings)
    stride = 1
    if total > MAX_POINTS:
        stride = (total + MAX_POINTS - 1) // MAX_POINTS
    simplified = []
    for ring in rings:
        thinned = ring[::stride]
        if len(thinned) < 3:
            thinned = ring[:3]
        if thinned[0] != thinned[-1]:
            thinned = list(thinned) + [thinned[0]]
        simplified.append(thinned)
    return simplified
