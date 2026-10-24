"""Contrato compartilhado pelo parser, banco e exportação."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal


@dataclass(frozen=True)
class Offer:
    listing_id: str
    title: str
    url: str
    price: Decimal
    previous_price: Decimal | None
    seller: str | None
    page: int
    collected_at: datetime
    marketplace: str = "mercadolivre"

    def __post_init__(self):
        if not self.listing_id or not self.title or not self.url or self.page < 1:
            raise ValueError("Oferta sem identidade, título, URL ou página válida.")
        if not self.price.is_finite() or self.price <= 0:
            raise ValueError("Preço deve ser positivo e finito.")
        if self.previous_price is not None and (
            not self.previous_price.is_finite() or self.previous_price <= 0
        ):
            raise ValueError("Preço anterior deve ser positivo e finito.")
        if self.collected_at.tzinfo is None or self.collected_at.utcoffset() is None:
            raise ValueError("Data de coleta deve ter fuso horário.")

    @property
    def observed_on(self):
        return self.collected_at.astimezone(timezone.utc).date()

    @property
    def discount(self):
        if self.previous_price is None or self.previous_price < self.price:
            return None
        return (1 - self.price / self.previous_price).quantize(Decimal("0.0001"))

    def to_dict(self):
        data = asdict(self)
        data["price"] = str(self.price)
        data["previous_price"] = (
            str(self.previous_price) if self.previous_price is not None else None
        )
        data["discount"] = str(self.discount) if self.discount is not None else None
        data["collected_at"] = self.collected_at.astimezone(timezone.utc).isoformat()
        return data
