from wanderlens.catalog.destinations import (
    JsonCatalog,
    bound_granularity,
    clean_destination,
    clean_name,
)
from wanderlens.core.models import Destination


def test_clean_name_strips_qualifier_and_normalizes():
    assert clean_name("Córdoba (city, Spain)") == "Córdoba"
    assert clean_name("Larissa (prefecture)") == "Larissa"
    assert clean_name("  black sea turkey ") == "Black Sea Turkey"


def test_clean_name_preserves_acronyms():
    assert clean_name("Kotor (MNE)") == "Kotor"


def test_granularity_is_bounded():
    assert bound_granularity("region") == "region"
    assert bound_granularity("other") == "area"
    assert bound_granularity("weird-kind") == "area"

    destination = Destination(id="x", name="X", lat=1, lon=1, country="Y", granularity="other")
    clean_destination(destination)
    assert destination.granularity == "area"


def test_catalog_deduplicates_by_normalized_name_and_country():
    a = Destination(id="a", name="Rhodes (city)", lat=1, lon=1, country="Greece")
    b = Destination(id="b", name="Rhodes", lat=1, lon=1, country="Greece")

    catalog = JsonCatalog([a, b])

    assert len(catalog.candidates()) == 1
    assert catalog.candidates()[0].name == "Rhodes"
