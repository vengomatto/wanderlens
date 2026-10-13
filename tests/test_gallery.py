from wanderlens.core.gallery import build_gallery


def test_gallery_is_deterministic():
    assert build_gallery().to_json() == build_gallery().to_json()


def test_gallery_relevant_destinations_are_in_catalog():
    gallery = build_gallery()
    ids = {destination.id for destination in gallery.destinations}
    assert gallery.relevant
    assert gallery.relevant <= ids
    assert set(gallery.vectors) == ids


def test_gallery_facets_present():
    gallery = build_gallery()
    assert gallery.facets
    assert all(facet.vector is not None for facet in gallery.facets)
