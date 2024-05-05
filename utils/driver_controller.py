import os

from selenium import webdriver
from dotenv import load_dotenv

from cfg import LoggingConfig

LoggingConfig.default_setup_logging(
    file_handler_path="logs/DriverControllerLOG.txt",
    file_handler_mode="a",
)
logger = LoggingConfig.get_logger(logger__name__=__name__)

load_dotenv()
class DriverController:

    __DRIVER_PATH = os.getenv("DRIVER_PATH")
    __TYPE_OF_DRIVER = os.getenv("TYPE_OF_DRIVER")
    __DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH")

    @staticmethod
    def start_driver(headless=True):

        logger.info("Driver solicitado")
        logger.info((
            "Variáveis de execução: " + "\n"
            + "DRIVER_PATH: " + DriverController.__DRIVER_PATH + "\n"
            + "TYPE_OF_DRIVER: " + DriverController.__TYPE_OF_DRIVER + "\n"
            + "DOWNLOAD_PATH: " + DriverController.__DOWNLOAD_PATH + "\n"
        ))

        if DriverController.__TYPE_OF_DRIVER == "FIREFOX":
            options = DriverController.driver_cfg_firefox(headless)
            driver = webdriver.Firefox(options=options)

        elif DriverController.__TYPE_OF_DRIVER == "CHROME":
            options = DriverController.driver_cfg_chrome(headless)
            driver = webdriver.Chrome(DriverController.__DRIVER_PATH,options=options)

        if (not driver):
            logger.info("Não foi possível iniciar o driver")
            raise RuntimeError


        logger.info("Driver retornado")

        return driver

    @staticmethod
    def driver_cfg_firefox(headless):
        from selenium.webdriver.firefox.options import Options

        options = Options()
        options.add_argument('window-size=400,800')

        if headless:
            options.add_argument('--headless')

        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", DriverController.__DOWNLOAD_PATH)
        options.set_preference("browser.download.useDownloadDir", True)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf, application/octet-stream")

        options.binary_location = DriverController.__DRIVER_PATH

        return options

    @staticmethod
    def driver_cfg_chrome(headless):
        from selenium.webdriver.chrome.options import Options

        options = Options()
        options.add_argument('window-size=400,800')

        if headless:
            options.add_argument('--headless')

        prefs = {
            "download.default_directory": DriverController.__DOWNLOAD_PATH,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }

        options.add_experimental_option("prefs", prefs)

        return options


if __name__ == '__main__':
    driver = DriverController.start_driver()