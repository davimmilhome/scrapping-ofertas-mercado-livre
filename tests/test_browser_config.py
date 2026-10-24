from dataclasses import replace
from unittest.mock import MagicMock, patch

import pytest
from selenium.common.exceptions import TimeoutException

from offers_spider.browser import Browser, FetchError
from offers_spider.config import Settings


@pytest.mark.parametrize(
    "settings",
    [
        {"app_env": "invalid"},
        {"pages": 0},
        {"timeout": 0},
        {"retries": -1},
        {"request_delay": -1},
        {"browser": "invalid"},
        {"base_url": "file:///tmp/x"},
        {"timeout": float("nan")},
        {"app_env": "production", "database_url": "sqlite:///output/prod.sqlite3"},
        {"pages": 101},
        {"timeout": 301},
        {"retries": 6},
        {"request_delay": 61},
        {"max_runtime": 0},
        {"max_runtime": 301},
        {"log_retention_days": 0},
        {"log_retention_days": 366},
        {"app_env": "production", "base_url": "http://example.com"},
        {"app_env": "production", "database_url": "mysql://user:pass@db/offers"},
    ],
)
def test_invalid_configuration(settings):
    with pytest.raises(ValueError):
        replace(Settings(), **settings)


def test_production_accepts_postgresql_and_https():
    settings = Settings(
        app_env="production",
        database_url="postgresql+psycopg://user:pass@db/offers",
        base_url="https://www.mercadolivre.com.br/ofertas",
    )
    assert settings.app_env == "production"


@pytest.mark.parametrize("browser_name", ["chrome", "firefox"])
def test_driver_lifecycle_and_service(browser_name):
    driver = MagicMock()
    driver.page_source = "<html>ok</html>"
    factory = "Chrome" if browser_name == "chrome" else "Firefox"
    with patch(f"offers_spider.browser.webdriver.{factory}", return_value=driver) as create:
        with patch("offers_spider.browser.WebDriverWait") as wait:
            settings = Settings(browser=browser_name, driver_path="driver.exe")
            with Browser(settings) as browser:
                assert browser.fetch("https://example.com") == "<html>ok</html>"
            wait.return_value.until.assert_called_once()
            driver.set_page_load_timeout.assert_called_once_with(settings.timeout)
            driver.set_script_timeout.assert_called_once_with(settings.timeout)
            assert create.call_args.kwargs["service"].path == "driver.exe"
    driver.quit.assert_called_once()


def test_retry_exhaustion_and_cleanup():
    driver = MagicMock()
    driver.page_source = "<html></html>"
    driver.get.side_effect = TimeoutException("timeout")
    with patch("offers_spider.browser.webdriver.Chrome", return_value=driver):
        with Browser(Settings(browser="chrome", retries=2, request_delay=0)) as browser:
            with pytest.raises(FetchError):
                browser.fetch("https://example.com")
    assert driver.get.call_count == 3
    driver.quit.assert_called_once()


def test_site_error_page_is_reported():
    driver = MagicMock()
    driver.page_source = "<p>Hubo un error accediendo a esta pagina...</p>"
    with patch("offers_spider.browser.webdriver.Chrome", return_value=driver):
        with patch("offers_spider.browser.WebDriverWait") as wait:
            wait.return_value.until.side_effect = TimeoutException()
            with Browser(Settings(browser="chrome", retries=0)) as browser:
                with pytest.raises(FetchError, match="página de erro"):
                    browser.fetch("https://www.mercadolivre.com.br/ofertas")
    driver.quit.assert_called_once()


def test_env_file_and_environment_precedence(monkeypatch, tmp_path):
    path = tmp_path / "config.env"
    path.write_text("APP_ENV=staging\nPAGES=3\nHEADLESS=false\nBROWSER=firefox\n", encoding="utf-8")
    monkeypatch.setenv("PAGES", "5")
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("HEADLESS", raising=False)
    monkeypatch.delenv("BROWSER", raising=False)
    settings = Settings.from_env(path)
    assert settings.pages == 5
    assert settings.app_env == "staging"
    assert not settings.headless
    assert settings.browser == "firefox"


def test_environment_app_env_overrides_env_file(monkeypatch, tmp_path):
    path = tmp_path / "config.env"
    path.write_text("APP_ENV=staging\n", encoding="utf-8")
    monkeypatch.setenv("APP_ENV", "test")
    assert Settings.from_env(path).app_env == "test"
