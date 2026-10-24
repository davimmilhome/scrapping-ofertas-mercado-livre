import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError

from offers_spider.storage import Repository, export_json, normalize_database_url


def test_generic_postgresql_url_uses_psycopg3():
    url = normalize_database_url("postgresql://user:pass@db/offers")
    assert url.drivername == "postgresql+psycopg"


def test_daily_upsert_history_and_different_listings(tmp_path, offers):
    repo = Repository(f"sqlite:///{tmp_path / 'data.sqlite3'}")
    try:
        repo.save(offers)
        repo.save(offers)
        assert len(repo.rows()) == 2
        updated = replace(
            offers[0],
            price=Decimal("900"),
            collected_at=offers[0].collected_at + timedelta(hours=1),
        )
        repo.save([updated])
        repo.save([offers[0]])  # coleta antiga não sobrescreve nova
        row = next(row for row in repo.rows() if row["listing_id"] == offers[0].listing_id)
        assert row["price"] == Decimal("900")
        repo.save([replace(updated, collected_at=updated.collected_at + timedelta(days=1))])
        repo.save([replace(updated, listing_id="MLB999", title=offers[0].title)])
        assert len(repo.rows()) == 4
        assert len({row["id"] for row in repo.rows()}) == 4
    finally:
        repo.close()


def test_batch_failure_rolls_back_and_propagates(offers):
    repo = Repository("sqlite:///:memory:")
    calls = 0

    def fail_second_insert(connection, cursor, statement, parameters, context, executemany):
        nonlocal calls
        if statement.startswith("INSERT"):
            calls += 1
            if calls == 2:
                raise SQLAlchemyError("simulated failure")

    event.listen(repo.engine, "before_cursor_execute", fail_second_insert)
    try:
        with pytest.raises(SQLAlchemyError):
            repo.save(offers)
        assert repo.rows() == []
    finally:
        repo.close()


def test_json_decimal_precision_and_atomic_replace(tmp_path, offers):
    path = tmp_path / "out" / "offers.json"
    export_json(offers, path)
    content = path.read_text(encoding="utf-8")
    data = json.loads(content)
    assert data[0]["price"] == "999.50"
    assert data[0]["collected_at"].endswith("+00:00")
    with patch("offers_spider.storage.os.replace", side_effect=OSError("disk error")):
        with pytest.raises(OSError):
            export_json([], path)
    assert path.read_text(encoding="utf-8") == content
    assert list(path.parent.glob("*.tmp")) == []


def test_offsets_are_normalized_before_upsert(offers):
    repo = Repository("sqlite:///:memory:")
    try:
        original = offers[0]
        newer = replace(
            original,
            price=Decimal("800.00"),
            collected_at=(original.collected_at + timedelta(hours=1)).astimezone(
                timezone(timedelta(hours=-3))
            ),
        )
        repo.save([original, newer])
        repo.save([original])
        assert repo.rows()[0]["price"] == Decimal("800.00")
        assert repo.rows()[0]["collected_at"].hour == 13
    finally:
        repo.close()


def test_collection_run_log_and_retention(tmp_path):
    repo = Repository(f"sqlite:///{tmp_path / 'runs.sqlite3'}")
    now = datetime.now(timezone.utc)
    try:
        current = repo.start_run(
            app_env="test",
            pages_requested=2,
            max_duration_seconds=300,
            started_at=now,
        )
        repo.finish_run(
            current,
            status="succeeded",
            finished_at=now + timedelta(seconds=2),
            duration_seconds=2,
            pages_ok=2,
            offers_found=4,
        )
        old = repo.start_run(
            app_env="test",
            pages_requested=1,
            max_duration_seconds=300,
            started_at=now - timedelta(days=3),
        )
        assert old != current
        assert repo.prune_runs(retention_days=2, stale_after_seconds=600, now=now) == 1
        rows = repo.run_rows()
        assert len(rows) == 1
        assert rows[0]["run_id"] == current
        assert rows[0]["status"] == "succeeded"
        assert rows[0]["offers_found"] == 4
    finally:
        repo.close()
