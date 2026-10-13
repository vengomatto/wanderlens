from __future__ import annotations

import re

"""One shared attribute vocabulary so photo-derived tags and catalog attributes
map into the same space (see design.md risk: vocabulary mismatch).

Synonyms are matched on word boundaries, never as arbitrary substrings, so
``"art"`` no longer matches ``"earth"``. A synonym ending in ``*`` matches any
token with that prefix (for stems such as ``archaeolog*``); a multi-word synonym
matches as a contiguous token sequence.
"""

VOCABULARY: dict[str, tuple[str, ...]] = {
    "coastal": ("coast", "coastline", "coastal", "seaside", "shore", "seafront"),
    "beach": ("beach", "sand", "sandy"),
    "cliffs": ("cliff", "rocky shore"),
    "water": ("water", "sea", "ocean", "azure", "turquoise", "bay", "harbour view"),
    "boats": ("boat", "yacht", "sailing", "marina", "harbour", "harbor", "ferry", "port"),
    "mountains": ("mountain", "peak", "alps", "summit", "ridge"),
    "hiking": ("hiking", "trek", "trail", "walk", "footpath"),
    "snow": ("snow", "glacier", "winter"),
    "lake": ("lake", "fjord", "reservoir"),
    "river": ("river", "canal", "waterfall"),
    "forest": ("forest", "woodland", "pine", "wood"),
    "wildlife": ("wildlife", "animal", "bird", "birds"),
    "city": ("city", "urban", "town", "skyline", "metropolis", "downtown"),
    "village": ("village", "hamlet"),
    "old_town": ("old town", "historic centre", "historic center", "medieval", "picturesque"),
    "architecture": (
        "architecture",
        "building",
        "cathedral",
        "church",
        "fort",
        "abbey",
        "monastery",
        "castle",
        "palace",
        "tower",
    ),
    "food": ("food", "cuisine", "restaurant", "seafood", "market", "vineyard", "winery", "cafe"),
    "museum": ("museum", "gallery", "art", "heritage", "exhibit"),
    "history": ("history", "ruins", "archaeolog*", "ancient"),
    "camping": ("camping", "campervan", "campsite", "tent"),
    "nature": ("nature", "landscape", "greenery", "scenery", "wilderness", "valley"),
    "sunset": ("sunset", "sunrise", "golden hour"),
    "desert": ("desert", "dune"),
    "countryside": ("countryside", "rural", "farm", "farmland"),
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _has_sequence(tokens: list[str], parts: list[str]) -> bool:
    span = len(parts)
    return any(tokens[i : i + span] == parts for i in range(len(tokens) - span + 1))


def _token_matches(token: str, synonym: str) -> bool:
    """Match a whole token, allowing a regular plural suffix (word boundaries)."""
    if synonym.endswith("*"):
        return token.startswith(synonym[:-1])
    return token == synonym or token == synonym + "s" or token == synonym + "es"


def _matches(tokens: list[str], token_set: set[str], synonyms: tuple[str, ...]) -> bool:
    for synonym in synonyms:
        if " " in synonym:
            if _has_sequence(tokens, synonym.split()):
                return True
        elif any(_token_matches(token, synonym) for token in token_set):
            return True
    return False


def canonicalize(tag: str) -> list[str]:
    """Map a free-text tag (or running text) into canonical attributes.

    Matching is word-boundary based: a synonym matches a whole token (or a
    contiguous token sequence), so substrings such as ``"art"`` inside
    ``"earth"`` never match.
    """
    tokens = _tokens(tag)
    if not tokens:
        return []
    token_set = set(tokens)
    return [
        canonical
        for canonical, synonyms in VOCABULARY.items()
        if _matches(tokens, token_set, synonyms)
    ]


def canonical_set(tags) -> set[str]:
    result: set[str] = set()
    for tag in tags:
        result.update(canonicalize(tag))
    return result
