"""Configuração validada, carregada apenas ao iniciar a aplicação."""

import math
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

MAX_PAGES = 100
MAX_TIMEOUT = 300
MAX_RETRIES = 5
MAX_REQUEST_DELAY = 60
MAX_LOG_RETENTION_DAYS = 365


@dataclass(frozen=True)
class Settings:
    app_env: str = "development"
    database_url: str = "sqlite:///output/offers.sqlite3"
    output_path: Path = Path("output/offers.json")
    base_url: str = "https://www.mercadolivre.com.br/ofertas"
    pages: int = 1
    browser: str = "firefox"
    headless: bool = True
    timeout: float = 20
    retries: int = 2
    request_delay: float = 1
    max_runtime: float = 300
    log_retention_days: int = 30
    driver_path: str | None = None

    def __post_init__(self):
        if self.app_env not in {"development", "test", "staging", "production"}:
            raise ValueError("APP_ENV deve ser development, test, staging ou production.")
        if (
            self.pages < 1
            or self.pages > MAX_PAGES
            or self.timeout <= 0
            or self.timeout > MAX_TIMEOUT
            or self.retries < 0
            or self.retries > MAX_RETRIES
            or self.request_delay < 0
            or self.request_delay > MAX_REQUEST_DELAY
            or self.max_runtime <= 0
            or self.max_runtime > MAX_TIMEOUT
            or self.log_retention_days < 1
            or self.log_retention_days > MAX_LOG_RETENTION_DAYS
            or not math.isfinite(self.timeout)
            or not math.isfinite(self.request_delay)
            or not math.isfinite(self.max_runtime)
        ):
            raise ValueError(
                "PAGES entre 1 e 100, TIMEOUT entre 0 e 300, RETRIES entre 0 e 5 "
                "REQUEST_DELAY entre 0 e 60, MAX_RUNTIME entre 0 e 300 "
                "e LOG_RETENTION_DAYS entre 1 e 365."
            )
        if self.browser not in {"chrome", "firefox"}:
            raise ValueError("BROWSER deve ser chrome ou firefox.")
        url = urlparse(self.base_url)
        if url.scheme not in {"http", "https"} or not url.netloc:
            raise ValueError("BASE_URL deve ser uma URL HTTP(S).")
        if not self.database_url:
            raise ValueError("DATABASE_URL não pode ser vazia.")
        if self.app_env == "production":
            if not self.database_url.lower().startswith("postgresql"):
                raise ValueError("Produção exige uma URL PostgreSQL; SQLite não é permitido.")
            if url.scheme != "https":
                raise ValueError("Produção exige BASE_URL com HTTPS.")

    @classmethod
    def from_env(cls, env_file: Path | None = None):
        if env_file is not None and not env_file.is_file():
            raise ValueError("Arquivo de configuração não encontrado.")
        load_dotenv(env_file or Path(".env"), override=False)
        boolean = os.getenv("HEADLESS", "true").lower()
        if boolean not in {"true", "false", "1", "0"}:
            raise ValueError("HEADLESS deve ser true ou false.")
        return cls(
            app_env=os.getenv("APP_ENV", "development").lower(),
            database_url=os.getenv("DATABASE_URL", cls.database_url),
            output_path=Path(os.getenv("OUTPUT_PATH", "output/offers.json")),
            base_url=os.getenv("BASE_URL", cls.base_url),
            pages=int(os.getenv("PAGES", "1")),
            browser=os.getenv("BROWSER", "firefox").lower(),
            headless=boolean in {"true", "1"},
            timeout=float(os.getenv("TIMEOUT", "20")),
            retries=int(os.getenv("RETRIES", "2")),
            request_delay=float(os.getenv("REQUEST_DELAY", "1")),
            max_runtime=float(os.getenv("MAX_RUNTIME", "300")),
            log_retention_days=int(os.getenv("LOG_RETENTION_DAYS", "30")),
            driver_path=os.getenv("DRIVER_PATH") or None,
        )
