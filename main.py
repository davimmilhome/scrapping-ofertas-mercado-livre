from cfg import LoggingConfig

from scrappers import (
    MLScrapper
)

from utils import (
    TimeUtils
)

LoggingConfig.default_setup_logging(
    file_handler_path="logs/main.log",
    file_handler_mode="a",
)

logger = LoggingConfig.get_logger(logger__name__=__name__)

ddmmyy_date = TimeUtils.get_current_ddmmyy_date()
ML_filename = ("ML" + "_" + ddmmyy_date + "_")


if __name__ == '__main__':
    #MLScrapper.ML_offer_pages_scrapper(output_path=f"output/{ML_filename}offers.json")
    pass
