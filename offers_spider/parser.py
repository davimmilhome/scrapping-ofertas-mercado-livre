"""Parser puro: HTML entra, ofertas e rejeições saem, sem navegador ou banco."""

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qs, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup, Tag

from .domain import Offer

CARD_SELECTOR = ".promotion-item, .poly-card, .ui-search-result__wrapper"
READY_SELECTOR = (
    ".promotion-item .andes-money-amount__fraction, "
    ".poly-card .poly-price__current .andes-money-amount__fraction, "
    ".ui-search-result__wrapper .andes-money-amount__fraction"
)


class ParseError(ValueError):
    pass


@dataclass
class ParseResult:
    offers: list[Offer]
    errors: list[str]


def money(amount: Tag) -> Decimal:
    fraction = amount.select_one(".andes-money-amount__fraction")
    cents = amount.select_one(".andes-money-amount__cents")
    if fraction:
        value = fraction.get_text(strip=True).replace(".", "").replace(" ", "")
        if cents:
            value += "." + cents.get_text(strip=True)
    else:
        value = re.sub(r"[^0-9,.-]", "", amount.get_text(" ", strip=True))
        value = value.replace(".", "").replace(",", ".")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ParseError("Preço ilegível.") from exc
    if not result.is_finite() or result <= 0:
        raise ParseError("Preço inválido.")
    return result.quantize(Decimal("0.01"))


def listing_identity(url: str) -> tuple[str, str]:
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise ParseError("Link de anúncio inválido.")
    params = parse_qs(parts.query)
    # Mercado Livre places `wid` in the tracking fragment on some cards.
    params.update(parse_qs(parts.fragment))
    # Offers pages use `item_id` for catalog links and `wid` for /up links.
    item_id = params.get("item_id", params.get("wid", [""]))[0]
    match = re.search(r"MLB-?(\d+)", item_id, re.I)
    if match is None:
        match = re.search(r"MLB-?(\d+)", parts.path, re.I)
    if match is None:
        raise ParseError("Link sem identificador MLB; não é seguro deduplicar.")
    identity = "MLB" + match.group(1)
    query = "item_id=" + identity if item_id else ""
    canonical = urlunsplit((parts.scheme, parts.netloc.lower(), parts.path.rstrip("/"), query, ""))
    return identity, canonical


def parse_html(html: str, *, page: int, collected_at: datetime, base_url: str) -> ParseResult:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(CARD_SELECTOR)
    cards = [card for card in cards if card.select_one(CARD_SELECTOR) is None]
    if not cards:
        raise ParseError("Nenhum cartão reconhecido: layout mudou, página vazia ou bloqueada.")
    offers, errors = [], []
    for index, card in enumerate(cards, 1):
        try:
            link = card.select_one(
                "a.poly-component__title, a.promotion-item__link-container, a.ui-search-link"
            )
            title = card.select_one(
                ".poly-component__title, .promotion-item__title, .ui-search-item__title"
            )
            if not link or not title or not link.get("href"):
                raise ParseError("Título ou link ausente.")
            listing_id, url = listing_identity(urljoin(base_url, link["href"]))
            previous = card.select_one("s.andes-money-amount, .andes-money-amount--previous")
            current = card.select_one(
                ".poly-price__current .andes-money-amount, "
                ".andes-money-amount-combo__main-container .andes-money-amount"
            )
            if current is None:
                current = next(
                    (
                        amount
                        for amount in card.select(".andes-money-amount")
                        if amount is not previous
                        and amount.name != "s"
                        and not amount.find_parent("s")
                        and "andes-money-amount--previous" not in amount.get("class", [])
                    ),
                    None,
                )
            if current is None:
                raise ParseError("Preço atual ausente.")
            seller_node = card.select_one(".poly-component__seller, .promotion-item__seller")
            seller = seller_node.get_text(" ", strip=True) if seller_node else None
            if seller:
                seller = re.sub(r"^(por|vendido por)\s+", "", seller, flags=re.I)
            offers.append(
                Offer(
                    listing_id=listing_id,
                    title=title.get_text(" ", strip=True),
                    url=url,
                    price=money(current),
                    previous_price=money(previous) if previous else None,
                    seller=seller,
                    page=page,
                    collected_at=collected_at,
                )
            )
        except (ValueError, TypeError) as exc:
            errors.append(f"Página {page}, cartão {index}: {exc}")
    if not offers:
        raise ParseError("Todos os cartões foram rejeitados. " + "; ".join(errors))
    return ParseResult(offers, errors)
