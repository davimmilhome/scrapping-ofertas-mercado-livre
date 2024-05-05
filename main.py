from cfg import LoggingConfig

from scrappers import (
    MLScrapper
)

LoggingConfig.default_setup_logging(
    file_handler_path="logs/mainLOG.txt",
    file_handler_mode="a",
)
logger = LoggingConfig.get_logger(logger__name__=__name__)


if __name__ == '__main__':
    MLScrapper.ML_offer_pages_scrapper(output_path="output/offers.json")
