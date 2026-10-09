from __future__ import annotations

from pathlib import Path
from typing import Optional

from wanderlens.core.taste import haversine_km


def load_country_names(path: str | Path) -> dict[str, str]:
    """Parse GeoNames countryInfo.txt into {country_code: country_name}."""
    names: dict[str, str] = {}
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) >= 5:
            names[cols[0]] = cols[4]
    return names


class GeoNamesIndex:
    """Offline nearest-place lookup over a GeoNames ``cities*.txt`` file."""

    def __init__(self, cities_path: str | Path, countries_path: Optional[str | Path] = None):
        self._cities: list[tuple[str, float, float, str]] = []
        text = Path(cities_path).read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            cols = line.split("\t")
            if len(cols) < 15:
                continue
            try:
                name = cols[1]
                lat = float(cols[4])
                lon = float(cols[5])
                country_code = cols[8]
            except (ValueError, IndexError):
                continue
            self._cities.append((name, lat, lon, country_code))
        self._countries: dict[str, str] = {}
        if countries_path is not None and Path(countries_path).exists():
            self._countries = load_country_names(countries_path)

    @property
    def size(self) -> int:
        return len(self._cities)

    def nearest(self, lat: float, lon: float, max_km: float = 50.0) -> Optional[tuple[str, str]]:
        best = None
        best_km = max_km
        for name, clat, clon, code in self._cities:
            dist = haversine_km(lat, lon, clat, clon)
            if dist < best_km:
                best_km = dist
                best = (name, code)
        if best is None:
            return None
        name, code = best
        return name, self._countries.get(code, code)
