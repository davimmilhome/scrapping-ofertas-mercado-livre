"""Um navegador por execução, espera explícita e tentativas limitadas."""

import logging
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .config import Settings
from .parser import READY_SELECTOR

logger = logging.getLogger(__name__)


class FetchError(RuntimeError):
    """Falha de navegação com diagnóstico apropriado para o usuário."""


class Browser:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.driver = None

    def __enter__(self):
        if self.settings.browser == "chrome":
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service

            factory = webdriver.Chrome
            headless = "--headless=new"
        else:
            from selenium.webdriver.firefox.options import Options
            from selenium.webdriver.firefox.service import Service

            factory = webdriver.Firefox
            headless = "-headless"
        options = Options()
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-sync")
        if self.settings.headless:
            options.add_argument(headless)
        if self.settings.browser == "firefox":
            options.set_preference("browser.download.useDownloadDir", False)
            options.set_preference("browser.helperApps.alwaysAsk.force", True)
            options.set_preference("dom.disable_open_during_load", True)
        kwargs = {"options": options}
        if self.settings.driver_path:
            kwargs["service"] = Service(executable_path=self.settings.driver_path)
        self.driver = factory(**kwargs)
        try:
            self.driver.set_page_load_timeout(self.settings.timeout)
            self.driver.set_script_timeout(self.settings.timeout)
        except Exception:
            self.driver.quit()
            raise
        return self

    def fetch(self, url: str) -> str:
        if self.driver is None:
            raise RuntimeError("Navegador não iniciado.")
        for attempt in range(self.settings.retries + 1):
            try:
                self.driver.get(url)
                WebDriverWait(self.driver, self.settings.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, READY_SELECTOR))
                )
                return self.driver.page_source
            except (TimeoutException, WebDriverException) as exc:
                if attempt == self.settings.retries:
                    detail = "Não foi possível carregar os preços dos cartões no prazo configurado."
                    try:
                        content = self.driver.page_source.lower()
                        if "hubo un error accediendo" in content:
                            detail = "O Mercado Livre retornou uma página de erro, sem ofertas."
                    except WebDriverException:
                        pass
                    raise FetchError(detail) from exc
                logger.warning("Falha de navegação; nova tentativa %s.", attempt + 1)
                time.sleep(self.settings.request_delay * (2**attempt))
        raise RuntimeError("Coleta sem resultado.")

    def __exit__(self, exc_type, exc, traceback):
        if self.driver is not None:
            try:
                self.driver.quit()
            except WebDriverException:
                logger.warning("Falha ao encerrar o navegador.", exc_info=True)
            finally:
                self.driver = None
