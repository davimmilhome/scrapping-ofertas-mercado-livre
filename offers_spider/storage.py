"""Snapshot diário por anúncio: repetição atualiza, novo dia mantém histórico."""

import json
import os
import tempfile
from datetime import timezone
from pathlib import Path

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    UniqueConstraint,
    create_engine,
    select,
)
from sqlalchemy.engine import make_url

from .domain import Offer

metadata = MetaData()
snapshots = Table(
    "offer_snapshots",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("marketplace", String(64), nullable=False),
    Column("listing_id", String(64), nullable=False),
    Column("observed_on", Date, nullable=False),
    Column("title", String(1024), nullable=False),
    Column("url", String(4096), nullable=False),
    Column("price", Numeric(18, 2), nullable=False),
    Column("previous_price", Numeric(18, 2)),
    Column("seller", String(1024)),
    Column("page", Integer, nullable=False),
    Column("collected_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("marketplace", "listing_id", "observed_on", name="uq_offer_daily"),
)


class Repository:
    def __init__(self, database_url: str):
        url = make_url(database_url)
        if url.get_backend_name() not in {"sqlite", "postgresql"}:
            raise ValueError("Banco suportado: SQLite ou PostgreSQL.")
        if url.get_backend_name() == "sqlite" and url.database not in {None, "", ":memory:"}:
            Path(url.database).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(url, pool_pre_ping=True, hide_parameters=True)
        try:
            metadata.create_all(self.engine)
        except Exception:
            self.engine.dispose()
            raise

    def save(self, offers: list[Offer]) -> int:
        if not offers:
            return 0
        if self.engine.dialect.name == "sqlite":
            from sqlalchemy.dialects.sqlite import insert
        else:
            from sqlalchemy.dialects.postgresql import insert
        with self.engine.begin() as connection:
            for offer in offers:
                statement = insert(snapshots).values(
                    marketplace=offer.marketplace,
                    listing_id=offer.listing_id,
                    observed_on=offer.observed_on,
                    title=offer.title,
                    url=offer.url,
                    price=offer.price,
                    previous_price=offer.previous_price,
                    seller=offer.seller,
                    page=offer.page,
                    collected_at=offer.collected_at.astimezone(timezone.utc),
                )
                statement = statement.on_conflict_do_update(
                    index_elements=["marketplace", "listing_id", "observed_on"],
                    set_={
                        name: getattr(statement.excluded, name)
                        for name in (
                            "title",
                            "url",
                            "price",
                            "previous_price",
                            "seller",
                            "page",
                            "collected_at",
                        )
                    },
                    where=statement.excluded.collected_at >= snapshots.c.collected_at,
                )
                connection.execute(statement)
        return len(offers)

    def rows(self):
        with self.engine.connect() as connection:
            return [dict(row) for row in connection.execute(select(snapshots)).mappings()]

    def close(self):
        self.engine.dispose()


def export_json(offers: list[Offer], path: Path):
    """Troca atômica impede deixar um JSON incompleto se a escrita falhar."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
        ) as stream:
            temporary = Path(stream.name)
            json.dump([offer.to_dict() for offer in offers], stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
