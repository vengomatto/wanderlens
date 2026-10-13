from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, Optional

from wanderlens.catalog.destinations import JsonCatalog, normalize_record

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKIVOYAGE_API = "https://en.wikivoyage.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "wanderlens/0.1 (+https://github.com/Vengomatto/wanderlens)"

_HEADING_RE = re.compile(r"=+\s*[^=\n]+?\s*=+")


def clean_extract(text: str, max_chars: Optional[int] = None) -> str:
    """Strip wikitext headings and cut at a sentence boundary (not mid-sentence)."""
    text = _HEADING_RE.sub(" ", text or "")
    text = " ".join(text.split())
    if max_chars and len(text) > max_chars:
        head = text[:max_chars]
        cut = max(head.rfind(". "), head.rfind("! "), head.rfind("? "))
        if cut > max_chars // 2:
            return head[: cut + 1].rstrip()
        return head.rsplit(" ", 1)[0].rstrip(" ,.;:") + "…"
    return text


def fetch_wikipedia_summary(
    name: str, country: str = "", session=None, timeout: int = 30
) -> str:
    """First-sentence Wikipedia intro for a place, via country-qualified search."""
    import requests

    session = session or requests
    response = session.get(
        WIKIPEDIA_API,
        params={
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f"{name} {country}".strip(),
            "gsrlimit": 1,
            "prop": "extracts",
            "exintro": 1,
            "explaintext": 1,
            "redirects": 1,
        },
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})
    if not pages:
        return ""
    page = next(iter(pages.values()))
    return clean_extract(page.get("extract", ""), 300)


def _strip_html(value: str) -> str:
    import re

    return " ".join(re.sub(r"<[^>]+>", " ", value or "").split())


def _meta(metadata: dict, key: str) -> str:
    entry = metadata.get(key) or {}
    return str(entry.get("value", "")) if isinstance(entry, dict) else ""


_LISTING = re.compile(
    r"\{\{\s*(see|do|eat|drink|sleep|buy|listing|marker|go)\b(.*?)\}\}", re.IGNORECASE | re.DOTALL
)
_PARAM = re.compile(r"\|\s*([a-zA-Z_]+)\s*=\s*([^|}]*)")


def parse_pois(wikitext: str) -> list[dict]:
    """Extract *see*/*do* points of interest (with coordinates) from Wikivoyage wikitext."""
    pois: list[dict] = []
    for match in _LISTING.finditer(wikitext or ""):
        params = {name.lower(): value.strip() for name, value in _PARAM.findall(match.group(2))}
        kind = match.group(1).lower()
        if kind in {"listing", "marker"}:
            kind = (params.get("type") or "").lower()
        if kind not in {"see", "do"}:
            continue
        name = params.get("name") or params.get("title")
        lat, lon = params.get("lat"), params.get("long") or params.get("lon")
        if not name or lat is None or lon is None:
            continue
        try:
            pois.append(
                {"name": _strip_html(name), "kind": kind, "lat": float(lat), "lon": float(lon)}
            )
        except ValueError:
            continue
    return pois


def fetch_wikivoyage_page(
    name: str, country: str = "", session=None, timeout: int = 30
) -> Optional[dict]:
    """Wikivoyage page for a place: travel prose, ids, external and itinerary links."""
    import requests

    session = session or requests
    response = session.get(
        WIKIVOYAGE_API,
        params={
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f"{name} {country}".strip(),
            "gsrlimit": 1,
            "prop": "extracts|info|pageprops|extlinks|links",
            "explaintext": 1,
            "exlimit": 1,
            "inprop": "url",
            "ppprop": "wikibase_item",
            "ellimit": 50,
            "llimit": 100,
            "redirects": 1,
        },
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})
    if not pages:
        return None
    page = next(iter(pages.values()))
    extract = clean_extract(page.get("extract", ""))
    wikidata_id = (page.get("pageprops") or {}).get("wikibase_item", "")
    external = [e.get("*", "") for e in page.get("extlinks", []) if e.get("*")]
    itineraries = [
        {"title": link.get("title", ""), "url": "https://en.wikivoyage.org/wiki/" + link.get("title", "").replace(" ", "_")}
        for link in page.get("links", [])
        if "itinerar" in link.get("title", "").lower()
    ]
    if not extract and not external and not itineraries:
        return None
    return {
        "title": page.get("title", ""),
        "page_url": page.get("fullurl", ""),
        "extract": extract,
        "wikidata_id": wikidata_id,
        "external_links": external,
        "itineraries": itineraries,
    }


def fetch_wikivoyage_wikitext(title: str, session=None, timeout: int = 30) -> str:
    import requests

    session = session or requests
    response = session.get(
        WIKIVOYAGE_API,
        params={"action": "parse", "page": title, "prop": "wikitext", "format": "json", "redirects": 1},
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json().get("parse", {}).get("wikitext", {}).get("*", "")


def fetch_wikipedia_media(
    name: str, country: str = "", session=None, timeout: int = 30, max_chars: int = 1500
) -> Optional[dict]:
    """Hero image + expanded extract + source link for a place, from Wikipedia."""
    import requests

    session = session or requests
    response = session.get(
        WIKIPEDIA_API,
        params={
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f"{name} {country}".strip(),
            "gsrlimit": 1,
            "prop": "extracts|pageimages|info",
            "explaintext": 1,
            "exintro": 1,
            "exlimit": 1,
            "piprop": "thumbnail",
            "pithumbsize": 1280,
            "inprop": "url",
            "redirects": 1,
        },
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})
    if not pages:
        return None
    page = next(iter(pages.values()))
    extract = clean_extract(page.get("extract", ""), max_chars)
    thumbnail = (page.get("thumbnail") or {}).get("source", "")
    if not extract and not thumbnail:
        return None
    return {
        "title": page.get("title", ""),
        "page_url": page.get("fullurl", ""),
        "extract": extract,
        "image_url": thumbnail,
        "image_license": "",
        "image_attribution": "Wikipedia",
    }


def fetch_commons_gallery(
    lat: float,
    lon: float,
    session=None,
    limit: int = 12,
    radius: int = 20000,
    timeout: int = 30,
    thumb_width: int = 1280,
) -> list[dict]:
    """A small gallery of Commons images geotagged near the coordinates."""
    import requests

    session = session or requests
    response = session.get(
        COMMONS_API,
        params={
            "action": "query",
            "format": "json",
            "generator": "geosearch",
            "ggscoord": f"{lat}|{lon}",
            "ggsradius": radius,
            "ggslimit": limit,
            "ggsnamespace": 6,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": thumb_width,
        },
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})
    return [image for image in (_image_from_info(page) for page in pages.values()) if image]


def _image_from_info(page: dict) -> Optional[dict]:
    info = (page.get("imageinfo") or [{}])[0]
    url = info.get("thumburl") or info.get("url")
    if not url:
        return None
    metadata = info.get("extmetadata") or {}
    return {
        "title": page.get("title", ""),
        "url": url,
        "width": int(info.get("width") or 0),
        "height": int(info.get("height") or 0),
        "mime": info.get("mime", ""),
        "license": _strip_html(_meta(metadata, "LicenseShortName")),
        "attribution": _strip_html(_meta(metadata, "Artist")),
        "categories": _strip_html(_meta(metadata, "Categories")),
        "source": "commons",
    }


def fetch_commons_imageinfo(
    titles: Iterable[str], session=None, width: int = 1280, timeout: int = 30
) -> list[dict]:
    """Resolve Commons file titles to image metadata, in batches."""
    import requests

    cleaned = [t for t in titles if t]
    if not cleaned:
        return []
    session = session or requests
    images: list[dict] = []
    for start in range(0, len(cleaned), 40):
        batch = cleaned[start : start + 40]
        response = session.get(
            COMMONS_API,
            params={
                "action": "query",
                "format": "json",
                "titles": "|".join(batch),
                "prop": "imageinfo",
                "iiprop": "url|size|mime|extmetadata",
                "iiurlwidth": width,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
        response.raise_for_status()
        for page in response.json().get("query", {}).get("pages", {}).values():
            image = _image_from_info(page)
            if image:
                images.append(image)
    return images


def fetch_wikidata_item_image(qid: str, session=None, timeout: int = 30) -> list[dict]:
    """The item's representative image (Wikidata P18), as an image record."""
    filename = fetch_wikidata_claim(qid, "P18", session=session, timeout=timeout)
    if not filename:
        return []
    return fetch_commons_imageinfo([f"File:{filename}"], session=session)


def fetch_wikipedia_article_images(
    title: str, session=None, timeout: int = 30, limit: int = 200
) -> list[str]:
    """File titles embedded in an encyclopedia article."""
    import requests

    response = (session or requests).get(
        WIKIPEDIA_API,
        params={
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "images",
            "imlimit": limit,
        },
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})
    if not pages:
        return []
    page = next(iter(pages.values()))
    return [image.get("title", "") for image in page.get("images", []) if image.get("title")]


def fetch_commons_category(
    category: str, session=None, timeout: int = 30, limit: int = 60
) -> list[dict]:
    """Files in a Commons category, with metadata."""
    import requests

    if not category:
        return []
    if not category.lower().startswith("category:"):
        category = f"Category:{category}"
    response = (session or requests).get(
        COMMONS_API,
        params={
            "action": "query",
            "format": "json",
            "generator": "categorymembers",
            "gcmtitle": category,
            "gcmtype": "file",
            "gcmlimit": limit,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": 1280,
        },
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})
    images = [_image_from_info(page) for page in pages.values()]
    return [image for image in images if image]


def fetch_wikidata_commons_category(qid: str, session=None, timeout: int = 30) -> Optional[str]:
    """The item's Commons category (Wikidata P373)."""
    return fetch_wikidata_claim(qid, "P373", session=session, timeout=timeout)


def fetch_wikidata_description(name: str, session=None, timeout: int = 30) -> str:
    """Concise Wikidata description for a place."""
    import requests

    session = session or requests
    response = session.get(
        WIKIDATA_API,
        params={
            "action": "wbsearchentities",
            "search": name,
            "language": "en",
            "format": "json",
            "limit": 1,
            "type": "item",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    results = response.json().get("search", [])
    return results[0].get("description", "") if results else ""


def enrich_records(records: list[dict], providers=None, delay: float = 0.0) -> list[dict]:
    """Attach a description to each record via a provider chain; never fail the batch.

    Providers are tried in order; the first non-empty description wins.
    """
    import time

    from wanderlens.catalog.providers import WikimediaProvider

    if providers is None:
        providers = [WikimediaProvider()]

    for record in records:
        if record.get("description"):
            continue
        description = ""
        for provider in providers:
            try:
                description = provider.describe(record.get("name", ""), record.get("countryName", "")) or ""
            except Exception:
                description = ""
            if description:
                break
        record["description"] = description
        if delay:
            time.sleep(delay)
    return records


def country_names_for_codes(countries_path: str | Path, codes) -> dict[str, str]:
    """Map GeoNames country codes (e.g. 'ES') to country names ('Spain')."""
    wanted = {code.upper() for code in codes}
    result: dict[str, str] = {}
    path = Path(countries_path)
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) >= 5 and cols[0].upper() in wanted:
            result[cols[0].upper()] = cols[4]
    return result


def country_code_for_name(countries_path: str | Path, name: str) -> Optional[str]:
    """Map a country name (e.g. 'Malta') to its GeoNames code ('MT')."""
    path = Path(countries_path)
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) >= 5 and cols[4].lower() == name.lower():
            return cols[0]
    return None


def load_geonames_cities(
    cities_path: str | Path,
    country_codes: Optional[Iterable[str]] = None,
    min_population: int = 0,
    limit: Optional[int] = None,
    countries_path: Optional[str | Path] = None,
) -> list[dict]:
    """Turn a GeoNames ``cities*.txt`` dump into raw Destination records."""
    codes = {c.upper() for c in country_codes} if country_codes else None
    country_names: dict[str, str] = {}
    if countries_path and Path(countries_path).exists():
        for line in Path(countries_path).read_text(encoding="utf-8", errors="replace").splitlines():
            if line and not line.startswith("#"):
                cols = line.split("\t")
                if len(cols) >= 5:
                    country_names[cols[0]] = cols[4]

    records: list[dict] = []
    for line in Path(cities_path).read_text(encoding="utf-8", errors="replace").splitlines():
        cols = line.split("\t")
        if len(cols) < 15:
            continue
        try:
            code = cols[8].upper()
            population = int(cols[14] or 0)
        except ValueError:
            continue
        if codes and code not in codes:
            continue
        if population < min_population:
            continue
        records.append(
            {
                "geonameId": cols[0],
                "name": cols[1],
                "latitude": float(cols[4]),
                "longitude": float(cols[5]),
                "countryName": country_names.get(code, code),
                "tags": [],
                "description": "",
            }
        )
        if limit and len(records) >= limit:
            break
    return records


def fetch_wikidata_candidates(query: str, timeout: int = 60) -> list[dict]:
    """Fetch Destination records from the Wikidata SPARQL endpoint."""
    import requests

    response = requests.get(
        WIKIDATA_ENDPOINT,
        params={"query": query, "format": "json"},
        headers={"Accept": "application/sparql-results+json", "User-Agent": "wanderlens/0.1"},
        timeout=timeout,
    )
    response.raise_for_status()
    bindings = response.json()["results"]["bindings"]
    records = []
    for row in bindings:
        try:
            records.append(
                {
                    "id": row["item"]["value"].rsplit("/", 1)[-1],
                    "label": row["itemLabel"]["value"],
                    "lat": float(row["lat"]["value"]),
                    "lon": float(row["lon"]["value"]),
                    "country": row.get("countryLabel", {}).get("value", ""),
                    "tags": [],
                    "description": row.get("itemDescription", {}).get("value", ""),
                }
            )
        except (KeyError, ValueError):
            continue
    return records


def build_catalog(records: dict[str, list[dict]]) -> JsonCatalog:
    destinations = []
    for source, items in records.items():
        for raw in items:
            destinations.append(normalize_record(source, raw))
    return JsonCatalog(destinations)


OPENLIBRARY_SEARCH = "https://openlibrary.org/search.json"
OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"


def fetch_openlibrary_books(place: str, session=None, limit: int = 8, timeout: int = 30) -> list[dict]:
    """Books tagged with a place, from Open Library."""
    import requests

    session = session or requests
    response = session.get(
        OPENLIBRARY_SEARCH,
        params={"q": f'place:"{place}"', "limit": limit, "fields": "title,author_name,key"},
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    books: list[dict] = []
    for doc in response.json().get("docs", []):
        title = doc.get("title")
        if not title:
            continue
        authors = doc.get("author_name") or []
        key = doc.get("key") or ""
        books.append(
            {
                "title": title,
                "author": authors[0] if authors else "",
                "url": f"https://openlibrary.org{key}" if key else "",
                "source": "openlibrary",
            }
        )
    return books


def fetch_wikidata_narrative_works(
    qid: str, instance_types: Iterable[str], session=None, timeout: int = 45, limit: int = 20
) -> list[dict]:
    """Works whose narrative location is ``qid``, filtered by instance-of types."""
    import requests

    if not qid:
        return []
    values = " ".join(f"wd:{t}" for t in instance_types)
    query = (
        "SELECT ?work ?workLabel WHERE {"
        f" ?work wdt:P840 wd:{qid} ."
        f" ?work wdt:P31/wdt:P279* ?type . VALUES ?type {{ {values} }}"
        " SERVICE wikibase:label { bd:serviceParam wikibase:language 'en'. }"
        f" }} LIMIT {limit}"
    )
    response = (session or requests).get(
        WIKIDATA_ENDPOINT,
        params={"query": query, "format": "json"},
        headers={"Accept": "application/sparql-results+json", "User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    works: list[dict] = []
    for row in response.json().get("results", {}).get("bindings", []):
        works.append(
            {
                "title": row.get("workLabel", {}).get("value", ""),
                "url": row.get("work", {}).get("value", ""),
                "source": "wikidata",
            }
        )
    return works


BOOK_TYPES = ("Q8261", "Q571", "Q47461344", "Q7725634")
FILM_TYPES = ("Q11424", "Q5398426", "Q506240")


def fetch_wikidata_claim(qid: str, prop: str, session=None, timeout: int = 30) -> Optional[str]:
    """First value of a Wikidata claim (e.g. P856 official website) for an entity."""
    import requests

    if not qid:
        return None
    try:
        response = (session or requests).get(
            WIKIDATA_API,
            params={"action": "wbgetentities", "ids": qid, "props": "claims", "format": "json"},
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
        response.raise_for_status()
        claims = response.json()["entities"][qid]["claims"]
        value = claims[prop][0]["mainsnak"]["datavalue"]["value"]
    except Exception:
        return None
    return value if isinstance(value, str) else None


def fetch_climate(lat: float, lon: float, session=None, years: int = 5, timeout: int = 45) -> list[dict]:
    """Per-month mean temperature and total precipitation from Open-Meteo."""
    import datetime as _dt
    import requests

    end = _dt.date.today() - _dt.timedelta(days=7)
    start = end.replace(year=end.year - years + 1, month=1, day=1)
    response = (session or requests).get(
        OPEN_METEO_ARCHIVE,
        params={
            "latitude": lat,
            "longitude": lon,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "daily": "temperature_2m_mean,precipitation_sum",
            "timezone": "UTC",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    daily = response.json().get("daily", {})
    temps: dict[int, list[float]] = {}
    precip: dict[int, list[float]] = {}
    for date, temp, rain in zip(
        daily.get("time", []),
        daily.get("temperature_2m_mean", []),
        daily.get("precipitation_sum", []),
    ):
        month = int(date[5:7])
        if temp is not None:
            temps.setdefault(month, []).append(temp)
        if rain is not None:
            precip.setdefault(month, []).append(rain)
    return [
        {
            "month": month,
            "temp_c": round(sum(temps[month]) / len(temps[month]), 1) if temps.get(month) else None,
            "precip_mm": round(sum(precip[month]) / len(precip[month]), 1) if precip.get(month) else None,
        }
        for month in range(1, 13)
    ]


def fetch_trip_weather(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    session=None,
    timeout: int = 45,
) -> Optional[dict]:
    """Actual mean temperature and precipitation for a trip's date range."""
    import requests

    response = (session or requests).get(
        OPEN_METEO_ARCHIVE,
        params={
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_mean,precipitation_sum",
            "timezone": "UTC",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    daily = response.json().get("daily", {})
    temps = [t for t in daily.get("temperature_2m_mean", []) if t is not None]
    rains = [p for p in daily.get("precipitation_sum", []) if p is not None]
    if not temps:
        return None
    return {
        "temp_c": round(sum(temps) / len(temps), 1),
        "precip_mm": round(sum(rains) / len(rains), 1) if rains else None,
        "month": int(start_date[5:7]),
    }
