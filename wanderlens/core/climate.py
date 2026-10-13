from __future__ import annotations

from typing import Optional

COLD = "cold"
MILD = "mild"
WARM = "warm"
HOT = "hot"

COMFORT_BAND_C = 6.0
SEASON_MONTHS = {
    "spring": (3, 4, 5),
    "summer": (6, 7, 8),
    "autumn": (9, 10, 11),
    "winter": (12, 1, 2),
}


def band(temp_c: Optional[float]) -> str:
    if temp_c is None:
        return ""
    if temp_c < 5:
        return COLD
    if temp_c < 15:
        return MILD
    if temp_c < 24:
        return WARM
    return HOT


def climate_profile(per_trip: list[dict]) -> dict:
    """Aggregate per-trip weather into a user climate preference."""
    temps = [t["temp_c"] for t in per_trip if t.get("temp_c") is not None]
    if not temps:
        return {}
    precip = [t["precip_mm"] for t in per_trip if t.get("precip_mm") is not None]
    month_counts: dict[int, int] = {}
    for trip in per_trip:
        month = trip.get("month")
        if month:
            month_counts[month] = month_counts.get(month, 0) + 1
    total = sum(month_counts.values()) or 1
    temp_mean = sum(temps) / len(temps)
    return {
        "temp_mean": round(temp_mean, 1),
        "precip_mean": round(sum(precip) / len(precip), 1) if precip else None,
        "band": band(temp_mean),
        "months": {month: count / total for month, count in month_counts.items()},
    }


def best_months(monthly: list[dict], profile: dict, limit: int = 5) -> list[int]:
    """Months within the comfort band and drier than the destination's median."""
    if not monthly or not profile or profile.get("temp_mean") is None:
        return []
    target = profile["temp_mean"]
    precip = [m["precip_mm"] for m in monthly if m.get("precip_mm") is not None]
    precip_cut = sorted(precip)[len(precip) // 2] if precip else None
    scored: list[tuple[float, int, int]] = []
    for entry in monthly:
        temp = entry.get("temp_c")
        if temp is None or abs(temp - target) > COMFORT_BAND_C:
            continue
        rain = entry.get("precip_mm")
        wet = 1 if (rain is not None and precip_cut is not None and rain > precip_cut) else 0
        scored.append((abs(temp - target), wet, entry["month"]))
    scored.sort()
    return [month for _, _, month in scored[:limit]]


def climate_match(monthly: list[dict], profile: dict) -> float:
    """A [0,1] score for how well a destination's climate fits the preference."""
    if not monthly or not profile or profile.get("temp_mean") is None:
        return 0.0
    target = profile["temp_mean"]
    temps = [m["temp_c"] for m in monthly if m.get("temp_c") is not None]
    if not temps:
        return 0.0
    close = sum(1 for temp in temps if abs(temp - target) <= COMFORT_BAND_C) / len(temps)
    rains = [m["precip_mm"] for m in monthly if m.get("precip_mm") is not None]
    profile_rain = profile.get("precip_mean")
    if rains and profile_rain is not None:
        dest_rain = sum(rains) / len(rains)
        rain_sim = max(0.0, 1.0 - abs(dest_rain - profile_rain) / 80.0)
    else:
        rain_sim = close
    return round(min(1.0, max(0.0, 0.6 * close + 0.4 * rain_sim)), 3)


def season_overlap(month_list: list[int], season: str) -> bool:
    months = SEASON_MONTHS.get((season or "").lower())
    if not months:
        return False
    return any(month in months for month in month_list or [])
