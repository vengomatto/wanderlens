from __future__ import annotations

"""One shared attribute vocabulary so photo-derived tags and catalog attributes
map into the same space (see design.md risk: vocabulary mismatch)."""

VOCABULARY: dict[str, tuple[str, ...]] = {
    "coastal": ("coast", "coastal", "seaside", "shore"),
    "beach": ("beach", "sand"),
    "cliffs": ("cliff", "rocky shore"),
    "water": ("water", "sea", "ocean", "azure", "turquoise", "bay"),
    "boats": ("boat", "yacht", "sailing", "marina", "harbour", "harbor"),
    "mountains": ("mountain", "peak", "alps", "summit"),
    "hiking": ("hiking", "trek", "trail", "walk"),
    "snow": ("snow", "glacier", "winter"),
    "lake": ("lake", "fjord"),
    "river": ("river", "canal"),
    "forest": ("forest", "woodland", "pine"),
    "wildlife": ("wildlife", "animal", "bird"),
    "city": ("city", "urban", "town", "skyline"),
    "village": ("village", "hamlet"),
    "old_town": ("old town", "historic centre", "historic center", "medieval"),
    "architecture": ("architecture", "building", "cathedral", "church", "fort"),
    "food": ("food", "cuisine", "restaurant", "seafood", "market"),
    "museum": ("museum", "gallery", "art"),
    "history": ("history", "ruins", "archaeolog"),
    "camping": ("camping", "campervan", "campsite", "tent"),
    "nature": ("nature", "landscape", "greenery", "scenery"),
    "sunset": ("sunset", "sunrise", "golden hour"),
    "desert": ("desert", "dune"),
    "countryside": ("countryside", "rural", "farm"),
}


def canonicalize(tag: str) -> list[str]:
    """Map a free-text tag into zero or more canonical attributes."""
    text = tag.lower().strip()
    matches: list[str] = []
    for canonical, synonyms in VOCABULARY.items():
        if any(syn in text for syn in synonyms):
            matches.append(canonical)
    return matches


def canonical_set(tags) -> set[str]:
    result: set[str] = set()
    for tag in tags:
        result.update(canonicalize(tag))
    return result
