from wanderlens.catalog.geonames import GeoNamesIndex

CITIES = (
    "2562305\tValletta\tValletta\t\t35.89972\t14.51472\tP\tPPLA\tMT\t\t\t\t\t\t\t\tn/a\t\tEurope/Malta\t2023-01-01\n"
    "3170647\tGenoa\tGenoa\t\t44.40478\t8.94439\tP\tPPLA\tIT\t\t\t\t\t\t\t\tn/a\t\tEurope/Rome\t2023-01-01\n"
)
COUNTRIES = "MT\tMLT\t470\tMT\tMalta\tValletta\t316000\tEurope\tMalta\tEUR\tEuro\t+356\t.mt\tMT\t^\n"


def _write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text)
    return path


def test_nearest_resolves_malta_coordinates(tmp_path):
    cities = _write(tmp_path, "cities.txt", CITIES)
    countries = _write(tmp_path, "countryInfo.txt", COUNTRIES)

    index = GeoNamesIndex(cities, countries)
    city, country = index.nearest(35.90, 14.51)

    assert city == "Valletta"
    assert country == "Malta"


def test_nearest_respects_max_distance(tmp_path):
    cities = _write(tmp_path, "cities.txt", CITIES)
    index = GeoNamesIndex(cities)
    assert index.nearest(0.0, 0.0, max_km=10) is None
