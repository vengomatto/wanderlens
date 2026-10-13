from __future__ import annotations

import re
from urllib.parse import parse_qs, unquote, urlparse

import requests

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) Wanderlens/0.1"
DDG_HTML_URL = "https://html.duckduckgo.com/html/"

_RESULT_RE = re.compile(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S)
_SNIPPET_RE = re.compile(r'class="result__snippet"[^>]*>(.*?)</a>', re.S)
_TAGS_RE = re.compile(r"<[^>]+>")


def _text(fragment: str) -> str:
    return _TAGS_RE.sub("", fragment).strip()


def _unwrap(url: str) -> str:
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlparse(url)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        values = parse_qs(parsed.query).get("uddg")
        if values:
            return unquote(values[0])
    return url


class DuckDuckGoSearchProvider:
    """Keyless web search over DuckDuckGo's HTML endpoint.

    No official API exists; the HTML endpoint is undocumented and can change, so
    callers MUST treat a result set as best-effort. Kept behind the
    ``SearchProvider`` seam so it stays injectable and testable.
    """

    name = "duckduckgo"

    def __init__(self, session=None, timeout: int = 30):
        self.session = session or requests
        self.timeout = timeout

    def search(self, query: str, limit: int = 5) -> list[dict]:
        response = self.session.post(
            DDG_HTML_URL,
            data={"q": query},
            headers={"User-Agent": USER_AGENT},
            timeout=self.timeout,
        )
        response.raise_for_status()
        html = response.text
        links = _RESULT_RE.findall(html)
        snippets = _SNIPPET_RE.findall(html)
        results: list[dict] = []
        for index, (url, title) in enumerate(links[:limit]):
            results.append(
                {
                    "title": _text(title),
                    "url": _unwrap(url),
                    "snippet": _text(snippets[index]) if index < len(snippets) else "",
                }
            )
        return results
