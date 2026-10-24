from datetime import datetime, timezone
from decimal import Decimal

import pytest

from offers_spider.parser import ParseError, listing_identity, parse_html


def parse(html):
    return parse_html(
        html,
        page=1,
        collected_at=datetime.now(timezone.utc),
        base_url="https://www.mercadolivre.com.br/ofertas",
    )


def test_prices_and_optional_fields(offers):
    assert len(offers) == 2  # wrapper com cartão interno não duplica
    assert offers[0].price == Decimal("999.50")
    assert offers[0].previous_price == Decimal("1299.90")
    assert offers[0].seller == "Loja Exemplo"
    assert offers[0].discount == Decimal("0.2311")
    assert offers[1].price == Decimal("150.00")
    assert offers[1].previous_price is None
    assert offers[1].seller is None
    assert offers[1].listing_id == "MLB987654321"


def test_tracking_does_not_change_identity():
    first = listing_identity("https://produto.mercadolivre.com.br/MLB-1234-x?track=1#abc")
    second = listing_identity("https://produto.mercadolivre.com.br/MLB-1234-x?track=2")
    assert first == second


def test_catalog_items_keep_distinct_sellers():
    first = listing_identity("https://www.mercadolivre.com.br/p/MLB123?item_id=MLB111")
    second = listing_identity("https://www.mercadolivre.com.br/p/MLB123?item_id=MLB222")
    assert first[0] != second[0]
    assert first[1] != second[1]


def test_up_links_use_wid_as_listing_identity():
    identity, canonical = listing_identity(
        "https://www.mercadolivre.com.br/produto/up/MLBU123?pdp_filters=x&wid=MLB987654321#tracking"
    )
    assert identity == "MLB987654321"
    assert canonical.endswith("?item_id=MLB987654321")


def test_wid_in_tracking_fragment_is_supported():
    identity, canonical = listing_identity(
        "https://www.mercadolivre.com.br/product/up/MLBU123?pdp_filters=x#position=1&wid=MLB987654321&sid=offers"
    )
    assert identity == "MLB987654321"
    assert canonical.endswith("?item_id=MLB987654321")


@pytest.mark.parametrize("html", ["<html>captcha</html>", '<div class="poly-card"></div>'])
def test_invalid_page_is_failure(html):
    with pytest.raises(ParseError):
        parse(html)


def test_broken_card_does_not_discard_valid_offers(html):
    result = parse(html + '<div class="poly-card"></div>')
    assert len(result.offers) == 2
    assert len(result.errors) == 1


def test_invalid_price_is_reported(html):
    result = parse(html.replace(">999<", ">not-money<"))
    assert len(result.offers) == 1
    assert len(result.errors) == 1


def test_missing_current_price_does_not_use_previous(html):
    html = html.replace(
        '<span class="andes-money-amount"><span class="andes-money-amount__fraction">999</span><span class="andes-money-amount__cents">50</span></span>',
        "",
    )
    result = parse(html)
    assert len(result.offers) == 1
    assert "Preço atual ausente" in result.errors[0]


@pytest.mark.parametrize("url", ["javascript:alert(1)", "https://example.com/no-item"])
def test_invalid_identity(url):
    with pytest.raises(ParseError):
        listing_identity(url)
