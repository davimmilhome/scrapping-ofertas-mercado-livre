"""Snapshot diário por anúncio: repetição atualiza, novo dia mantém histórico."""

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

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
    delete,
    or_,
    select,
    update,
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

collection_runs = Table(
    "collection_runs",
    metadata,
    Column("run_id", String(32), primary_key=True),
    Column("status", String(16), nullable=False),
    Column("app_env", String(16), nullable=False),
    Column("runner", String(32), nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("finished_at", DateTime(timezone=True)),
    Column("duration_seconds", Numeric(12, 3)),
    Column("max_duration_seconds", Numeric(12, 3), nullable=False),
    Column("pages_requested", Integer, nullable=False),
    Column("pages_ok", Integer, nullable=False, default=0),
    Column("offers_found", Integer, nullable=False, default=0),
    Column("failures_count", Integer, nullable=False, default=0),
    Column("rejected_count", Integer, nullable=False, default=0),
    Column("error_summary", String(1000)),
    Column("workflow_run_id", String(128)),
    Column("workflow_run_attempt", Integer),
)


def normalize_database_url(database_url: str):
    """Use the installed psycopg 3 driver for generic PostgreSQL URLs."""
    url = make_url(database_url)
    if url.get_backend_name() == "postgresql" and url.drivername == "postgresql":
        return url.set(drivername="postgresql+psycopg")
    return url


class Repository:
    def __init__(self, database_url: str):
        url = normalize_database_url(database_url)
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

    def start_run(
        self,
        *,
        app_env: str,
        pages_requested: int,
        max_duration_seconds: float,
        runner: str = "selenium",
        workflow_run_id: str | None = None,
        workflow_run_attempt: int | None = None,
        started_at: datetime | None = None,
    ) -> str:
        started_at = started_at or datetime.now(timezone.utc)
        run_id = uuid4().hex
        with self.engine.begin() as connection:
            connection.execute(
                collection_runs.insert().values(
                    run_id=run_id,
                    status="running",
                    app_env=app_env,
                    runner=runner,
                    started_at=started_at,
                    max_duration_seconds=max_duration_seconds,
                    pages_requested=pages_requested,
                    pages_ok=0,
                    offers_found=0,
                    failures_count=0,
                    rejected_count=0,
                    workflow_run_id=workflow_run_id,
                    workflow_run_attempt=workflow_run_attempt,
                )
            )
        return run_id

    def finish_run(
        self,
        run_id: str,
        *,
        status: str,
        finished_at: datetime,
        duration_seconds: float,
        pages_ok: int = 0,
        offers_found: int = 0,
        failures_count: int = 0,
        rejected_count: int = 0,
        error_summary: str | None = None,
    ) -> None:
        if status not in {"succeeded", "partial", "failed", "timed_out", "abandoned"}:
            raise ValueError("Status de execução inválido.")
        with self.engine.begin() as connection:
            connection.execute(
                update(collection_runs)
                .where(collection_runs.c.run_id == run_id)
                .values(
                    status=status,
                    finished_at=finished_at,
                    duration_seconds=duration_seconds,
                    pages_ok=pages_ok,
                    offers_found=offers_found,
                    failures_count=failures_count,
                    rejected_count=rejected_count,
                    error_summary=(error_summary or None)[:1000] if error_summary else None,
                )
            )

    def prune_runs(
        self,
        *,
        retention_days: int,
        stale_after_seconds: float,
        now: datetime | None = None,
    ) -> int:
        now = now or datetime.now(timezone.utc)
        retention_cutoff = now - timedelta(days=retention_days)
        stale_cutoff = now - timedelta(seconds=stale_after_seconds)
        with self.engine.begin() as connection:
            result = connection.execute(
                delete(collection_runs).where(
                    or_(
                        collection_runs.c.finished_at < retention_cutoff,
                        (
                            collection_runs.c.finished_at.is_(None)
                            & (collection_runs.c.started_at < retention_cutoff)
                        ),
                    ),
                )
            )
            connection.execute(
                update(collection_runs)
                .where(
                    collection_runs.c.status == "running",
                    collection_runs.c.started_at < stale_cutoff,
                )
                .values(status="abandoned", finished_at=now)
            )
        return result.rowcount or 0

    def run_rows(self):
        with self.engine.connect() as connection:
            return [dict(row) for row in connection.execute(select(collection_runs)).mappings()]

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
