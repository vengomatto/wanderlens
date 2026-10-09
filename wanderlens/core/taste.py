from __future__ import annotations

import math
from datetime import timedelta
from typing import Iterable

from wanderlens.core.models import Photo, Trip

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def cluster_into_trips(
    photos: Iterable[Photo],
    max_gap: timedelta = timedelta(hours=18),
    max_jump_km: float = 150.0,
) -> list[list[Photo]]:
    """Group photos into trips by capture-time gap and spatial jump.

    A new trip begins when the gap since the previous photo exceeds ``max_gap``
    or the distance from it exceeds ``max_jump_km`` (when both are geotagged).
    Photos without a capture time attach to the most recent trip.
    """
    photos = list(photos)
    timed = sorted((p for p in photos if p.taken_at), key=lambda p: p.taken_at)
    untimed = [p for p in photos if not p.taken_at]

    clusters: list[list[Photo]] = []
    for photo in timed:
        if not clusters:
            clusters.append([photo])
            continue
        prev = clusters[-1][-1]
        gap = photo.taken_at - prev.taken_at
        jump = None
        if None not in (prev.lat, prev.lon, photo.lat, photo.lon):
            jump = haversine_km(prev.lat, prev.lon, photo.lat, photo.lon)
        if gap > max_gap or (jump is not None and jump > max_jump_km):
            clusters.append([photo])
        else:
            clusters[-1].append(photo)

    if untimed:
        if clusters:
            clusters[-1].extend(untimed)
        else:
            clusters.append(untimed)
    return clusters


def to_trips(clusters: list[list[Photo]], reverse_geocoder=None) -> list[Trip]:
    trips: list[Trip] = []
    for i, photos in enumerate(clusters):
        trip = Trip(id=i, photos=photos)
        if reverse_geocoder is not None:
            located = [p for p in photos if p.lat is not None and p.lon is not None]
            if located:
                lat = sum(p.lat for p in located) / len(located)
                lon = sum(p.lon for p in located) / len(located)
                place = reverse_geocoder(lat, lon)
                if place:
                    trip.city, trip.country = place
        trips.append(trip)
    return trips


def geography_weights(trips: Iterable[Trip]) -> dict[str, float]:
    """Normalized country weights across trips that have a resolved country."""
    counts: dict[str, float] = {}
    for trip in trips:
        if trip.country:
            counts[trip.country] = counts.get(trip.country, 0.0) + 1.0
    total = sum(counts.values())
    if total == 0:
        return {}
    return {country: n / total for country, n in counts.items()}
