from wanderlens.core.vocabulary import canonicalize, canonical_set


def test_substring_false_positives_are_gone():
    assert canonicalize("earth") == []
    assert "museum" not in canonicalize("earth")
    assert "water" not in canonicalize("abbaye")


def test_seaside_is_coastal_not_water():
    attributes = canonicalize("seaside")
    assert "coastal" in attributes
    assert "water" not in attributes


def test_plural_tokens_match():
    assert "mountains" in canonicalize("mountains")
    assert "beach" in canonicalize("beaches")
    assert "boats" in canonicalize("boats")


def test_multiword_synonyms_match_as_sequence():
    assert "old_town" in canonicalize("a charming old town centre")
    assert "cliffs" in canonicalize("rugged rocky shore views")


def test_stem_prefix_matches():
    assert "history" in canonicalize("an archaeological site")


def test_expanded_vocabulary_terms():
    assert "architecture" in canonicalize("an ancient abbey")
    assert "architecture" in canonicalize("a hillside monastery")
    assert "food" in canonicalize("a local vineyard")
    assert "city" in canonicalize("the downtown metropolis")


def test_canonical_set_union():
    assert {"coastal", "city"} <= canonical_set(["seaside town", "urban skyline"])


def test_weather_terms():
    assert "weather" in canonicalize("a dramatic sky")
    assert "weather" in canonicalize("overcast morning")
