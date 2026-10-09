from wanderlens.catalog.destinations import (
    catalog_from_records,
    destination_from_dict,
    destination_to_dict,
    normalize_record,
)
from wanderlens.catalog.geonames import GeoNamesIndex
from wanderlens.core.models import Destination

WIKIDATA = {
    "id": "Q123",
    "label": "Cinque Terre",
    "lat": 44.13,
    "lon": 9.71,
    "country": "Italy",
    "tags": ["coastal", "hiking"],
    "description": "Five coastal villages.",
}

GEONAMES = {
    "geonameId": 3170647,
    "name": "Genoa",
    "latitude": 44.40478,
    "longitude": 8.94439,
    "countryName": "Italy",
    "tags": ["port", "old_town"],
}


def test_destination_round_trips():
    original = Destination(
        id="wd:Q1", name="X", lat=1.5, lon=2.5, country="Y", attributes=["coastal"], description="d"
    )
    restored = destination_from_dict(destination_to_dict(original))
    assert restored == original


def test_two_sources_normalize_to_same_shape(tmp_path):
    catalog = catalog_from_records({"wikidata": [WIKIDATA], "geonames": [GEONAMES]})

    assert len(catalog) == 2
    names = {d.name for d in catalog.candidates()}
    assert names == {"Cinque Terre", "Genoa"}
    for destination in catalog.candidates():
        assert isinstance(destination, Destination)
        assert destination.lat and destination.lon and destination.country == "Italy"

    cache = tmp_path / "catalog.json"
    catalog.save(cache)
    reloaded = type(catalog).load(cache)
    assert {d.name for d in reloaded.candidates()} == names


def test_offline_geo_name_resolution(tmp_path):
    cities = tmp_path / "cities.txt"
    cities.write_text(
        "2562305\tValletta\tValletta\t\t35.89972\t14.51472\tP\tPPLA\tMT\t\t\t\t\t\t\t\tn/a\t\tEurope/Malta\t2023-01-01\n"
    )
    index = GeoNamesIndex(cities)

    destination = normalize_record(
        "wikidata",
        {"id": "Q1", "label": "Somewhere", "lat": 35.90, "lon": 14.51, "country": ""},
    )
    city, country = index.nearest(destination.lat, destination.lon)
    assert city == "Valletta"
    assert country == "MT"
