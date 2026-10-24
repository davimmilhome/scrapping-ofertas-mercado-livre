import time
from urllib.parse import parse_qs, urlsplit

from offers_spider.browser import FetchError
from offers_spider.config import Settings
from offers_spider.service import collect, page_url


class FakeFetcher:
    def __init__(self, responses):
        self.responses = iter(responses)

    def fetch(self, url):
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


class SlowFetcher:
    def __init__(self, response, delay):
        self.response = response
        self.delay = delay

    def fetch(self, url):
        time.sleep(self.delay)
        return self.response


def test_page_url_preserves_filters():
    url = page_url("https://example.com/ofertas?category=x&page=99#anchor", 2)
    assert parse_qs(urlsplit(url).query) == {"category": ["x"], "page": ["2"]}
    assert not urlsplit(url).fragment


def test_partial_pages_continue_and_deduplicate(html):
    result = collect(
        Settings(pages=3, request_delay=0),
        FakeFetcher([html, OSError("network failed"), html]),
    )
    assert result.pages_ok == 2
    assert len(result.offers) == 2
    assert len(result.failures) == 1
    assert not result.complete


def test_all_failed():
    result = collect(Settings(), FakeFetcher(["<html>blocked</html>"]))
    assert result.offers == []
    assert not result.complete


def test_browser_failure_is_collected(html):
    result = collect(
        Settings(pages=2, request_delay=0),
        FakeFetcher([FetchError("página de erro"), html]),
    )
    assert len(result.offers) == 2
    assert "página de erro" in result.failures[0]


def test_rejected_card_marks_partial(html):
    result = collect(Settings(), FakeFetcher([html + '<div class="poly-card"></div>']))
    assert len(result.offers) == 2
    assert not result.complete
    assert len(result.rejected) == 1


def test_collection_stops_after_max_runtime(html):
    result = collect(
        Settings(pages=2, request_delay=0, max_runtime=0.001),
        SlowFetcher(html, delay=0.01),
    )
    assert result.timed_out
    assert result.pages_ok == 1
    assert not result.complete
