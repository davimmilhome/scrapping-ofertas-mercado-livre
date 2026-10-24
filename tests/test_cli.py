import json
from unittest.mock import MagicMock

from offers_spider import cli
from offers_spider.config import Settings
from offers_spider.storage import Repository


def setup_cli(monkeypatch, tmp_path, responses):
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'data.sqlite3'}",
        output_path=tmp_path / "offers.json",
        request_delay=0,
    )
    monkeypatch.setattr(cli.Settings, "from_env", lambda _: settings)
    browser = MagicMock()
    browser.__enter__.return_value.fetch.side_effect = responses
    monkeypatch.setattr(cli, "Browser", lambda _: browser)
    return settings, browser


def test_full_flow_and_repeat(monkeypatch, tmp_path, html):
    settings, browser = setup_cli(monkeypatch, tmp_path, [html, html])
    assert cli.main([]) == 0
    assert cli.main([]) == 0
    assert browser.__exit__.call_count == 2
    assert len(json.loads(settings.output_path.read_text(encoding="utf-8"))) == 2
    repo = Repository(settings.database_url)
    try:
        assert len(repo.rows()) == 2
        runs = repo.run_rows()
        assert len(runs) == 2
        assert all(run["status"] == "succeeded" for run in runs)
    finally:
        repo.close()


def test_partial_preserves_full_output(monkeypatch, tmp_path, html):
    settings, _ = setup_cli(monkeypatch, tmp_path, [html, OSError("offline")])
    settings.output_path.write_text("previous", encoding="utf-8")
    assert cli.main(["--pages", "2", "--json-only"]) == 2
    assert settings.output_path.read_text(encoding="utf-8") == "previous"
    assert (tmp_path / "offers.partial.json").exists()
    assert not (tmp_path / "data.sqlite3").exists()


def test_all_failed_preserves_output(monkeypatch, tmp_path):
    settings, _ = setup_cli(monkeypatch, tmp_path, ["<html>captcha</html>"])
    settings.output_path.write_text("previous", encoding="utf-8")
    assert cli.main(["--json-only"]) == 1
    assert settings.output_path.read_text(encoding="utf-8") == "previous"


def test_db_failure_is_not_success(monkeypatch, tmp_path, html):
    settings, _ = setup_cli(monkeypatch, tmp_path, [html])
    repository = MagicMock()
    repository.save.side_effect = RuntimeError("db offline")
    monkeypatch.setattr(cli, "Repository", lambda _: repository)
    assert cli.main([]) == 1
    assert not settings.output_path.exists()
    repository.close.assert_called_once()


def test_invalid_options_do_not_start_browser(monkeypatch, tmp_path):
    _, browser = setup_cli(monkeypatch, tmp_path, [])
    assert cli.main(["--pages", "0"]) == 1
    browser.__enter__.assert_not_called()


def test_production_cli_override_rejects_sqlite(monkeypatch, tmp_path):
    _, browser = setup_cli(monkeypatch, tmp_path, [])
    assert cli.main(["--app-env", "production"]) == 1
    browser.__enter__.assert_not_called()
