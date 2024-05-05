import json
from concurrent.futures import ThreadPoolExecutor


from cfg import LoggingConfig

from parsers import (
    MLParser
)
LoggingConfig.default_setup_logging(
    file_handler_path="logs/mainLOG.txt",
    file_handler_mode="a",
)
logger = LoggingConfig.get_logger(logger__name__=__name__)


class MLScrapper:

    __ML_BASE_URL = "https://www.mercadolivre.com.br/ofertas?container_id=MLB779362-1&page="

    @staticmethod
    def ML_offer_pages_scrapper(output_path, number_of_pages=20):

        with ThreadPoolExecutor() as executor:
            thread_executor_results_list = list(executor.map(MLScrapper.get_page_result, range(1, number_of_pages + 1)))

        pages_results = {}
        for result in thread_executor_results_list:
            pages_results.update(result)

        with open(output_path, 'w') as json_file:
            json.dump(list(pages_results.values()), json_file)

    @staticmethod
    def get_page_result(page_number):
        complete_url = f"{MLScrapper.__ML_BASE_URL}{page_number}"
        page_result = MLParser.ML_promotion_page_parser(complete_url)
        return page_result

if __name__ == '__main__':
    pass