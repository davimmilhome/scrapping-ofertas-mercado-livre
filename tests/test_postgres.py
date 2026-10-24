"""Integração opt-in, executada pelo job PostgreSQL da CI."""

import os
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import delete

from offers_spider.storage import Repository, snapshots


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"), reason="PostgreSQL de testes não configurado"
)
def test_postgres_upsert_and_history(offers):
    repository = Repository(os.environ["TEST_DATABASE_URL"])
    identity = "test-" + uuid4().hex
    offer = replace(offers[0], listing_id=identity)
    try:
        repository.save([offer, offer])
        updated = replace(
            offer, price=Decimal("800.50"), collected_at=offer.collected_at + timedelta(hours=1)
        )
        repository.save([updated])
        repository.save([offer])
        repository.save([replace(updated, collected_at=updated.collected_at + timedelta(days=1))])
        rows = [row for row in repository.rows() if row["listing_id"] == identity]
        assert len(rows) == 2
        assert all(row["price"] == Decimal("800.50") for row in rows)
    finally:
        with repository.engine.begin() as connection:
            connection.execute(delete(snapshots).where(snapshots.c.listing_id == identity))
        repository.close()
