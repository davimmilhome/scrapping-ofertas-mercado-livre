import json
from concurrent.futures import ProcessPoolExecutor

from cfg import (
    LoggingConfig
)

from parsers import (
    MLParser
)

LoggingConfig.default_setup_logging(
    file_handler_path="logs/ML_scrapper.log",
    file_handler_mode="a",
)

logger = LoggingConfig.get_logger(logger__name__=__name__)


class MLScrapper:

    __ML_BASE_URL = "https://www.mercadolivre.com.br/ofertas?container_id=MLB779362-1&page="

    @staticmethod
    def get_ML_pages_results(number_of_pages=20, json_output=False):
        with ProcessPoolExecutor() as executor:
            process_executor_results_list = list(
                executor.map(
                    MLScrapper.get_single_page_result,
                    range(1, number_of_pages + 1)
                )
            )

        ml_pages_results = {}
        for result in process_executor_results_list:
            ml_pages_results.update(result)

        if json_output:
            output_path = f"output/offers.json"
            with open(output_path, 'w') as json_file:
                json.dump(list(ml_pages_results.values()), json_file)

        return ml_pages_results

    @staticmethod
    def get_single_page_result(page_number):
        complete_url = f"{MLScrapper.__ML_BASE_URL}{page_number}"
        page_result = MLParser.ML_promotion_page_parser(complete_url)
        return page_result

if __name__ == '__main__':
    MLScrapper.get_single_page_result(14)
    pass
