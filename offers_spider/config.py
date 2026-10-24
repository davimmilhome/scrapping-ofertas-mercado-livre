"""Configuração validada, carregada apenas ao iniciar a aplicação."""

import math
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///output/offers.sqlite3"
    output_path: Path = Path("output/offers.json")
    base_url: str = "https://www.mercadolivre.com.br/ofertas"
    pages: int = 1
    browser: str = "firefox"
    headless: bool = True
    timeout: float = 20
    retries: int = 2
    request_delay: float = 1
    driver_path: str | None = None

    def __post_init__(self):
        if (
            self.pages < 1
            or self.timeout <= 0
            or self.retries < 0
            or self.request_delay < 0
            or not math.isfinite(self.timeout)
            or not math.isfinite(self.request_delay)
        ):
            raise ValueError("PAGES >= 1, TIMEOUT > 0, RETRIES >= 0 e REQUEST_DELAY >= 0.")
        if self.browser not in {"chrome", "firefox"}:
            raise ValueError("BROWSER deve ser chrome ou firefox.")
        url = urlparse(self.base_url)
        if url.scheme not in {"http", "https"} or not url.netloc:
            raise ValueError("BASE_URL deve ser uma URL HTTP(S).")
        if not self.database_url:
            raise ValueError("DATABASE_URL não pode ser vazia.")

    @classmethod
    def from_env(cls, env_file: Path | None = None):
        if env_file is not None and not env_file.is_file():
            raise ValueError("Arquivo de configuração não encontrado.")
        load_dotenv(env_file or Path(".env"), override=False)
        boolean = os.getenv("HEADLESS", "true").lower()
        if boolean not in {"true", "false", "1", "0"}:
            raise ValueError("HEADLESS deve ser true ou false.")
        return cls(
            database_url=os.getenv("DATABASE_URL", cls.database_url),
            output_path=Path(os.getenv("OUTPUT_PATH", "output/offers.json")),
            base_url=os.getenv("BASE_URL", cls.base_url),
            pages=int(os.getenv("PAGES", "1")),
            browser=os.getenv("BROWSER", "firefox").lower(),
            headless=boolean in {"true", "1"},
            timeout=float(os.getenv("TIMEOUT", "20")),
            retries=int(os.getenv("RETRIES", "2")),
            request_delay=float(os.getenv("REQUEST_DELAY", "1")),
            driver_path=os.getenv("DRIVER_PATH") or None,
        )
