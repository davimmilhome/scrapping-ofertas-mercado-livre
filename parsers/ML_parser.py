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

        ID_MARKETPLACE = '1'
        scrapped_json = {}

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

        for idx, item in enumerate(offers_li):
            link_offer = item.find(
                'a', attrs={'class': 'promotion-item__link-container'})['href']
            name_product = item.find(
                'p', attrs={'class': 'promotion-item__title'}).text

            previous_value = item.find(
                's', attrs={'class': 'andes-money-amount andes-money-amount'
                                     '-combo__previous-value andes-money-amount--previous andes-'
                                     'money-amount--cents-comma'}
            )

            value_offer_text = item.find(
                'span', attrs={'class': 'andes-money-amount__fraction'}).text
            value_offer_text = value_offer_text.replace('.', '')
            value_offer_cents = item.find(
                'span', attrs={'class': 'andes-money-amount__cents andes-money'
                                        '-amount__cents--superscript-24'}
            )
            if value_offer_cents:
                value_offer_cents = value_offer_cents.text
                value_offer = (
                        value_offer_text + '.' + value_offer_cents
                )
                value_offer = float(value_offer)
            else:
                value_offer = float(value_offer_text)

            if previous_value:
                previous_value = previous_value.text
                """ 
                As duas linhas abaixo no tratamento de valores antigos
                tem a inteção de corrigir o texto disposto pelo ML
                uma vez que o valor não vem separado do texto
                """
                previous_value = (previous_value.replace('R$','').replace('.', ''))
                previous_value = int(previous_value)

                discout_offer_decimals = 1 - (value_offer / previous_value)
                discout_offer_decimals = round(discout_offer_decimals, 2)
            else:
                discout_offer_decimals = None

            name_store = item.find(
                'span', attrs={'class': 'promotion-item__seller'}
            )
            if name_store:
                name_store = name_store.text[4:]

            elif name_store == None:
                name_store = "SEM LOJA NA PÁGINA"

            single_offer_json = {
                'link_offer': link_offer,
                'name_product': name_product,
                'previous_value': previous_value,
                'value_offer': value_offer,
                'discount_offer_decimals': discout_offer_decimals,
                'name_store': name_store,
                'number_of_offer_page': number_of_offer_page,
                'id_makertplace' : ID_MARKETPLACE,
                'date_time_offer': TimeUtils.get_current_iso_datetime(),
            }

            """
            armazenar as informações de cada product_dict
             individualmente no dicionário, 
             usando o link do product_dict como chave.
            """
            scrapped_json[link_offer] = single_offer_json

        return scrapped_json

if __name__ == '__main__':
    dict = MLParser.ML_promotion_page_parser(
        ML_promotion_page_url="https://www.mercadolivre.com.br/ofertas?container_id=MLB779362-1&page=1")

    print(dict)
