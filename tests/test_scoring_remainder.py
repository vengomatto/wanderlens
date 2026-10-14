import numpy as np

from wanderlens.core.models import Destination
from wanderlens.core.recommend import rank_destinations, taste_attribute_weights
from wanderlens.pipeline.recommend import _recency_factor


def _dest(name, attrs):
    return Destination(id=name, name=name, lat=1.0, lon=1.0, country="X", attributes=attrs)


def test_anti_match_penalises_generic_only_match():
    generic = [_dest(f"g{i}", ["city"]) for i in range(6)]
    rare = _dest("rare", ["glacier"])
    vectors = {d.id: np.ones(2, dtype=np.float32) for d in generic + [rare]}
    taste = np.ones(2, dtype=np.float32)
    tags = taste_attribute_weights({"coastal": 1.0})  # user's interest is absent from the pool

    off = rank_destinations(taste, generic + [rare], vectors=vectors, taste_tags=tags)
    on = rank_destinations(
        taste, generic + [rare], vectors=vectors, taste_tags=tags, anti_match_weight=0.5
    )

    assert on[0].destination.id == "rare"
    assert off[0].destination.id != "rare"


def test_anti_match_off_by_default():
    generic = [_dest(f"g{i}", ["city"]) for i in range(6)]
    rare = _dest("rare", ["glacier"])
    vectors = {d.id: np.ones(2, dtype=np.float32) for d in generic + [rare]}
    taste = np.ones(2, dtype=np.float32)
    tags = taste_attribute_weights({"coastal": 1.0})

    a = [r.destination.id for r in rank_destinations(taste, generic + [rare], vectors=vectors, taste_tags=tags)]
    b = [
        r.destination.id
        for r in rank_destinations(taste, generic + [rare], vectors=vectors, taste_tags=tags, anti_match_weight=0.0)
    ]
    assert a == b


def test_recency_factor():
    assert _recency_factor(None, 365) == 1.0
    assert _recency_factor("2024-01-01T00:00:00", 0) == 1.0
    old = _recency_factor("2020-01-01T00:00:00", 365)
    assert 0.0 < old < 1.0
