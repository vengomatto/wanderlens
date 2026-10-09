from wanderlens.catalog.fetch import load_geonames_cities

CITIES = (
    "2562305\tValletta\tValletta\t\t35.89972\t14.51472\tP\tPPLA\tMT\t\t\t\t\t\t90000\tn/a\t\tEurope/Malta\t2023-01-01\n"
    "3170647\tGenoa\tGenoa\t\t44.40478\t8.94439\tP\tPPLA\tIT\t\t\t\t\t\t580000\tn/a\t\tEurope/Rome\t2023-01-01\n"
    "3170648\tTiny\tTiny\t\t44.0\t8.0\tP\tPPL\tIT\t\t\t\t\t\t100\tn/a\t\tEurope/Rome\t2023-01-01\n"
)
COUNTRIES = "MT\tMLT\t470\tMT\tMalta\tValletta\t316000\tEurope\tMalta\tEUR\tEuro\t+356\t.mt\tMT\t^\nIT\tITA\t380\tIT\tItaly\tRome\t60360000\tEurope\tItaly\tEUR\tEuro\t+39\t.it\tIT\t^\n"


def test_load_geonames_filter_by_population(tmp_path):
    cities = tmp_path / "cities.txt"
    cities.write_text(CITIES)
    countries = tmp_path / "countryInfo.txt"
    countries.write_text(COUNTRIES)

    records = load_geonames_cities(cities, min_population=50000, countries_path=countries)

    assert {r["name"] for r in records} == {"Valletta", "Genoa"}
    assert all(r["countryName"] in {"Malta", "Italy"} for r in records)


def test_load_geonames_filter_by_country_and_limit(tmp_path):
    cities = tmp_path / "cities.txt"
    cities.write_text(CITIES)

    records = load_geonames_cities(cities, country_codes=["IT"], limit=1)

    assert len(records) == 1
    assert records[0]["name"] == "Genoa"
