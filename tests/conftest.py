from datetime import datetime, timezone
from pathlib import Path

import pytest

from offers_spider.parser import parse_html


@pytest.fixture
def html():
    return (Path(__file__).parent / "fixtures" / "offers.html").read_text(encoding="utf-8")


@pytest.fixture
def offers(html):
    return parse_html(
        html,
        page=1,
        collected_at=datetime(2026, 1, 10, 12, tzinfo=timezone.utc),
        base_url="https://www.mercadolivre.com.br/ofertas",
    ).offers
