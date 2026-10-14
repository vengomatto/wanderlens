import numpy as np

from wanderlens.core.models import Destination
from wanderlens.core.recommend import rank_destinations, taste_attribute_weights


def _dest(name, attributes):
    return Destination(id=name, name=name, lat=1.0, lon=1.0, country="X", attributes=attributes)


def test_calibrate_normalizes_and_preserves_order():
    a = _dest("a", ["coastal", "beach", "water"])
    b = _dest("b", ["coastal"])
    vectors = {
        "a": np.ones(2, dtype=np.float32),
        "b": np.ones(2, dtype=np.float32),
    }
    taste = np.ones(2, dtype=np.float32)
    tags = taste_attribute_weights({"coastal": 1.0, "beach": 1.0, "water": 1.0})

    raw = rank_destinations(taste, [a, b], vectors=vectors, taste_tags=tags)
    calibrated = rank_destinations(
        taste, [a, b], vectors=vectors, taste_tags=tags, calibrate=True
    )

    assert raw[0].destination.id == "a"
    assert calibrated[0].destination.id == "a"
    assert calibrated[0].attribute_score == raw[0].attribute_score  # raw reported
    assert calibrated[0].score <= 1.0 + 1e-9
    assert calibrated[0].score > calibrated[1].score


def test_calibrate_off_by_default_matches_explicit_false():
    a = _dest("a", ["coastal"])
    b = _dest("b", ["beach"])
    vectors = {"a": np.array([1.0, 0.0], dtype=np.float32), "b": np.array([0.0, 1.0], dtype=np.float32)}
    taste = np.array([1.0, 0.0], dtype=np.float32)
    tags = taste_attribute_weights({"coastal": 1.0})

    default = [r.destination.id for r in rank_destinations(taste, [a, b], vectors=vectors, taste_tags=tags)]
    explicit = [
        r.destination.id
        for r in rank_destinations(taste, [a, b], vectors=vectors, taste_tags=tags, calibrate=False)
    ]
    assert default == explicit
