from wanderlens.catalog.search import DuckDuckGoSearchProvider

HTML = """
<html><body>
<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fkotor&amp;rut=abc">Kotor travel guide</a>
<a class="result__snippet">A walled coastal town in Montenegro.</a>
<a class="result__a" href="https://direct.example.org/bay">Bay of Kotor</a>
<a class="result__snippet">Stunning fjord-like bay.</a>
</body></html>
"""


class FakeResponse:
    def __init__(self, text):
        self.text = text
        self.status_code = 200

    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self, text):
        self.text = text
        self.calls = 0

    def post(self, url, **kwargs):
        self.calls += 1
        return FakeResponse(self.text)


def test_duckduckgo_parses_and_unwraps():
    session = FakeSession(HTML)
    results = DuckDuckGoSearchProvider(session=session).search("Kotor", limit=5)

    assert session.calls == 1
    assert results[0]["title"] == "Kotor travel guide"
    assert results[0]["url"] == "https://example.com/kotor"
    assert "coastal town" in results[0]["snippet"]
    assert results[1]["url"] == "https://direct.example.org/bay"
