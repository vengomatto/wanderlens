import json

from wanderlens.catalog.regions import (
    MAX_POINTS,
    NOMINATIM_SEARCH,
    point_count,
    resolve_region,
)
from wanderlens.core.models import Destination


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload

    def get(self, url, **kwargs):
        return FakeResponse(self.payload)


POLYGON = {
    "type": "Polygon",
    "coordinates": [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]],
}


def test_precise_polygon_when_available():
    destination = Destination(id="wy:algarve", name="Algarve", lat=37.0, lon=-8.0, country="Portugal")
    session = FakeSession([{"geojson": POLYGON}])

    geojson, kind, radius = resolve_region(destination, session=session)

    assert kind == "precise"
    assert radius is None
    feature = json.loads(geojson)
    assert feature["geometry"]["type"] == "Polygon"


def test_approximate_circle_when_no_boundary():
    destination = Destination(
        id="wy:cinque-terre", name="Cinque Terre", lat=44.1, lon=9.7, country="Italy", granularity="region"
    )
    session = FakeSession([])

    geojson, kind, radius = resolve_region(destination, session=session)

    assert kind == "approximate"
    assert radius == 40.0
    feature = json.loads(geojson)
    assert feature["geometry"]["type"] == "Point"
    assert feature["geometry"]["coordinates"] == [9.7, 44.1]


def test_no_coordinates_yields_nothing():
    destination = Destination(id="x", name="X", lat=None, lon=None)
    geojson, kind, radius = resolve_region(destination)
    assert (geojson, kind, radius) == ("", "", None)


def test_large_polygon_is_simplified_and_valid():
    ring = [[float(i), float(i)] for i in range(5000)] + [[0.0, 0.0]]
    destination = Destination(id="wy:big", name="Big", lat=1.0, lon=1.0, country="X")
    session = FakeSession([{"geojson": {"type": "Polygon", "coordinates": [ring]}}])

    geojson, kind, _ = resolve_region(destination, session=session)
    feature = json.loads(geojson)
    geometry = feature["geometry"]

    assert kind == "precise"
    assert point_count(geometry) <= MAX_POINTS + len(geometry["coordinates"])
    for polygon_ring in geometry["coordinates"]:
        assert polygon_ring[0] == polygon_ring[-1]
        assert len(polygon_ring) <= MAX_POINTS + 1
