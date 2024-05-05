from urllib.parse import urlparse, parse_qs


from cfg import LoggingConfig
from utils import (
    ContentController,
    TimeUtils,
)

LoggingConfig.default_setup_logging(
    file_handler_path="logs/ML_parser.log",
    file_handler_mode="a",
)
logger = LoggingConfig.get_logger(logger__name__=__name__)
class MLParser:

    @staticmethod
    def ML_promotion_page_parser(ML_promotion_page_url):

        soup = ContentController.get_site_content(ML_promotion_page_url)

        logger.info("Iniciando parser pela página de promoção")

        parsed_url = urlparse(ML_promotion_page_url)
        query_params = parse_qs(parsed_url.query)


        number_of_offer_page = query_params.get('page', [''])[0]

        if number_of_offer_page:
            number_of_offer_page = int(number_of_offer_page)
        else:
            number_of_offer_page = None  # Valor padrão se não houver número da


        offers_ol = soup.find('ol', attrs={'class': 'items_container'})
        offers_li = offers_ol.findAll('li')

        products_dict = {}

        for idx, item in enumerate(offers_li):
            product_link = item.find(
                'a', attrs={'class': 'promotion-item__link-container'})['href']
            product_name = item.find(
                'p', attrs={'class': 'promotion-item__title'}).text

            previous_value = item.find(
                's', attrs={'class': 'andes-money-amount andes-money-amount'
                                     '-combo__previous-value andes-money-amount--previous andes-'
                                     'money-amount--cents-comma'}
            )

            actual_value_text = item.find(
                'span', attrs={'class': 'andes-money-amount__fraction'}).text
            actual_value_text = actual_value_text.replace('.', '')
            actual_value_cents = item.find(
                'span', attrs={'class': 'andes-money-amount__cents andes-money'
                                        '-amount__cents--superscript-24'}
            )
            if actual_value_cents:
                actual_value_cents = actual_value_cents.text
                actual_value = (
                        actual_value_text + '.' + actual_value_cents
                )
                actual_value = float(actual_value)
            else:
                actual_value = float(actual_value_text)

            if previous_value:
                previous_value = previous_value.text
                """ 
                As duas linhas abaixo no tratamento de valores antigos
                tem a inteção de corrigir o texto disposto pelo ML
                uma vez que o valor não vem separado do texto
                """
                previous_value = (previous_value.replace('R$','').replace('.', ''))
                previous_value = int(previous_value)

                discount = 1 - (actual_value / previous_value)
                discount = round(discount, 2)
            else:
                discount = None

            store = item.find(
                'span', attrs={'class': 'promotion-item__seller'}
            )
            if store:
                store = store.text[4:]

            product_dict = {
                'product_link': product_link,
                'product_name': product_name,
                'previous_value': previous_value,
                'actual_value': actual_value,
                'discount': discount,
                'store': store,
                'number_of_offer_page': number_of_offer_page,
                'market_place' : 'MERCADO LIVRE',
                'timestamp': TimeUtils.get_current_iso_datetime(),
            }

            """
            armazenar as informações de cada product_dict
             individualmente no dicionário, 
             usando o link do product_dict como chave.
            """
            products_dict[product_link] = product_dict

        return products_dict

if __name__ == '__main__':
    products_dict = MLParser.ML_promotion_page_parser(
        ML_promotion_page_url="https://www.mercadolivre.com.br/ofertas?container_id=MLB779362-1&page=1")

    print(products_dict)
