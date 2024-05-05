from time import sleep
from bs4 import BeautifulSoup

from utils import (
    DriverController
)

from cfg import LoggingConfig

LoggingConfig.default_setup_logging(
    file_handler_path="logs/content_controller.log",
    file_handler_mode="a",
)
logger = LoggingConfig.get_logger(logger__name__=__name__)
class ContentController:

    @staticmethod
    def get_site_content(url):

        driver = DriverController.start_driver()

        try:
            logger.info(f"Tentando pegar as infos da página: {url}")

            driver.get(url)
            sleep(0.5)  # Espera a página carregar
            page_content = driver.page_source
            soup = BeautifulSoup(page_content, 'html.parser')  # Objeto BS

            logger.info("Retornando informações da página")
            return soup
        finally:
            driver.quit()

