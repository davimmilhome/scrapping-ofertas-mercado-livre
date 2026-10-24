"""Orquestração testável com um coletor injetado."""

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .browser import FetchError
from .config import Settings
from .domain import Offer
from .parser import ParseError, parse_html


class Fetcher(Protocol):
    def fetch(self, url: str) -> str: ...


@dataclass
class Collection:
    offers: list[Offer] = field(default_factory=list)
    pages_ok: int = 0
    failures: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)

    @property
    def complete(self):
        return not self.failures and not self.rejected


def page_url(base_url: str, page: int) -> str:
    parts = urlsplit(base_url)
    query = [(key, value) for key, value in parse_qsl(parts.query) if key != "page"]
    query.append(("page", str(page)))
    return urlunsplit(parts._replace(query=urlencode(query), fragment=""))


def collect(settings: Settings, fetcher: Fetcher) -> Collection:
    result = Collection()
    unique = {}
    for page in range(1, settings.pages + 1):
        if page > 1:
            time.sleep(settings.request_delay)
        try:
            html = fetcher.fetch(page_url(settings.base_url, page))
            parsed = parse_html(
                html,
                page=page,
                collected_at=datetime.now(timezone.utc),
                base_url=settings.base_url,
            )
            result.pages_ok += 1
            result.rejected.extend(parsed.errors)
            for offer in parsed.offers:
                unique.setdefault((offer.marketplace, offer.listing_id), offer)
        except (FetchError, ParseError, OSError) as exc:
            detail = str(exc).splitlines()
            result.failures.append(
                f"Página {page}: {type(exc).__name__}: {detail[0] if detail else ''}"
            )
    result.offers = sorted(unique.values(), key=lambda offer: (offer.page, offer.listing_id))
    return result
