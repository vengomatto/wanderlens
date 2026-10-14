import numpy as np

from wanderlens.core.models import Destination
from wanderlens.core.recommend import rank_destinations


def _d(name):
    return Destination(id=name, name=name, lat=1.0, lon=1.0, country="X")


def _vectors():
    return {
        "a": np.array([1.0, 0.0], dtype=np.float32),
        "b": np.array([1.0, 0.0], dtype=np.float32),
    }


def test_liked_outranks_equal():
    taste = np.array([1.0, 0.0], dtype=np.float32)
    ranked = rank_destinations(
        taste, [_d("a"), _d("b")], vectors=_vectors(), top_k=2, feedback={"b": "like"}
    )
    assert ranked[0].destination.id == "b"


def test_disliked_is_pushed_down():
    taste = np.array([1.0, 0.0], dtype=np.float32)
    ranked = rank_destinations(
        taste, [_d("a"), _d("b")], vectors=_vectors(), top_k=2, feedback={"a": "dislike"}
    )
    assert ranked[0].destination.id == "b"


def test_no_feedback_leaves_ranking_unchanged():
    taste = np.array([1.0, 0.0], dtype=np.float32)
    without = [r.destination.id for r in rank_destinations(taste, [_d("a"), _d("b")], vectors=_vectors())]
    empty = [
        r.destination.id
        for r in rank_destinations(taste, [_d("a"), _d("b")], vectors=_vectors(), feedback={})
    ]
    assert without == empty


def test_taste_bias_reorders_when_enabled():
    taste = np.array([1.0, 1.0], dtype=np.float32)
    vectors = {
        "a": np.array([1.0, 0.0], dtype=np.float32),
        "b": np.array([0.0, 1.0], dtype=np.float32),
    }
    bias = np.array([0.0, 1.0], dtype=np.float32)

    ranked = rank_destinations(
        taste, [_d("a"), _d("b")], vectors=vectors, top_k=2,
        taste_bias=bias, taste_bias_weight=0.5,
    )

    assert ranked[0].destination.id == "b"
