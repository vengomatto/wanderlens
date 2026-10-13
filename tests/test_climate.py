import numpy as np

from wanderlens.core.climate import band, best_months, climate_match, climate_profile, season_overlap
from wanderlens.core.models import Destination
from wanderlens.core.recommend import rank_destinations

MONTHLY = [
    {"month": m, "temp_c": t, "precip_mm": p}
    for m, t, p in [
        (1, 5, 40), (2, 6, 30), (3, 12, 20), (4, 16, 15), (5, 20, 10), (6, 24, 5),
        (7, 27, 2), (8, 27, 3), (9, 23, 8), (10, 18, 20), (11, 11, 40), (12, 6, 50),
    ]
]


def test_temperature_bands():
    assert band(-2) == "cold"
    assert band(10) == "mild"
    assert band(20) == "warm"
    assert band(30) == "hot"
    assert band(None) == ""


def test_climate_profile_shape():
    profile = climate_profile(
        [{"temp_c": 22, "precip_mm": 5, "month": 7}, {"temp_c": 20, "precip_mm": 10, "month": 8}]
    )
    assert profile["temp_mean"] == 21.0
    assert profile["band"] == "warm"
    assert abs(sum(profile["months"].values()) - 1) < 1e-9


def test_climate_profile_empty():
    assert climate_profile([]) == {}


def test_best_months_within_band():
    profile = {"temp_mean": 24.0, "precip_mean": 5.0, "months": {7: 1.0}}
    best = best_months(MONTHLY, profile)
    assert 7 in best
    assert 1 not in best
    assert all(m in {5, 6, 7, 8, 9} for m in best)


def test_climate_match_bounds():
    profile = {"temp_mean": 24.0, "precip_mean": 5.0}
    assert climate_match(MONTHLY, profile) > 0.5
    assert climate_match([], profile) == 0.0
    assert climate_match(MONTHLY, {}) == 0.0


def test_season_overlap():
    assert season_overlap([6, 7], "summer") is True
    assert season_overlap([1, 2], "summer") is False
    assert season_overlap([], "winter") is False


def _vectors():
    return {"a": np.ones(3, dtype=np.float32), "b": np.ones(3, dtype=np.float32)}


def test_climate_bias_reorders_when_enabled():
    taste = np.ones(3, dtype=np.float32)
    ranked = rank_destinations(
        taste,
        [Destination(id="a", name="A", lat=1, lon=1, country="X"),
         Destination(id="b", name="B", lat=1, lon=1, country="X")],
        vectors=_vectors(),
        top_k=2,
        climate={"b": 1.0},
        climate_weight=0.5,
    )
    assert ranked[0].destination.id == "b"


def test_climate_off_by_default():
    taste = np.ones(3, dtype=np.float32)
    destinations = [
        Destination(id="a", name="A", lat=1, lon=1, country="X"),
        Destination(id="b", name="B", lat=1, lon=1, country="X"),
    ]
    without = [r.destination.id for r in rank_destinations(taste, destinations, vectors=_vectors())]
    with_climate = [
        r.destination.id
        for r in rank_destinations(
            taste, destinations, vectors=_vectors(), climate={"b": 1.0}, climate_weight=0.0
        )
    ]
    assert without == with_climate


def test_season_prefers_best_months():
    taste = np.ones(3, dtype=np.float32)
    ranked = rank_destinations(
        taste,
        [Destination(id="a", name="A", lat=1, lon=1, country="X"),
         Destination(id="b", name="B", lat=1, lon=1, country="X")],
        vectors=_vectors(),
        top_k=2,
        season="summer",
        best_months={"a": [1], "b": [7]},
    )
    assert ranked[0].destination.id == "b"
