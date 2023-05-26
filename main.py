import json
import time
from time import sleep
from multiprocessing import Pool

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


def get_site_content(url,pagina):
    """
    Obtém o conteúdo HTML de uma página específica do site Mercado Livre.

    :param pagina: Número da página a ser acessada.
    :type pagina: int
    :return: Objeto BeautifulSoup contendo o conteúdo da página.
    :rtype: BeautifulSoup
    """

    start_time = time.time()

    options = Options()
    options.add_argument('window-size=400,800')
    options.add_argument('--headless')
    navegador = webdriver.Firefox(options=options)
    try:
        navegador.get(url+str(pagina))
        sleep(1)  # Espera a página carregar
        page_content = navegador.page_source
        site_func = BeautifulSoup(page_content, 'html.parser')  # Objeto BS
        return site_func
    finally:
        navegador.quit()

        end_time = time.time()
        execution_time = round(end_time - start_time,2)
        print(
         f'- [LOG]: Get realizado na page n° {pagina}\n'
         f'- [LOG]: Tempo de execução da função get_site {execution_time}s\n'
        )

def process_page(pagina):

    start_time = time.time()

    url = (
        'https://www.mercadolivre.com.br/ofertas'
        '?container_id=MLB779362-1&page='
    )

    site = get_site_content(url,pagina)

    ofertas_ol = site.find('ol', attrs={'class': 'items_container'})
    ofertas_li = ofertas_ol.findAll('li')

    produtos = {}

    for idx, item in enumerate(ofertas_li):
        link_prod = item.find(
            'a', attrs={'class': 'promotion-item__link-container'})['href']
        nome_prod = item.find(
            'p', attrs={'class': 'promotion-item__title'}).text

        vl_antigo_prod = item.find(
            's', attrs={'class': 'andes-money-amount andes-money-amount'
            '-combo__previous-value andes-money-amount--previous andes-'
            'money-amount--cents-comma'}
        )

        vl_atual_prod_texto = item.find(
            'span', attrs={'class': 'andes-money-amount__fraction'}).text
        vl_atual_prod_texto = vl_atual_prod_texto.replace('.', '')
        vl_atual_prod_centavos = item.find(
            'span', attrs={'class': 'andes-money-amount__cents andes-money'
            '-amount__cents--superscript-24'}
        )
        if vl_atual_prod_centavos:
            vl_atual_prod_centavos = vl_atual_prod_centavos.text
            vl_atual_prod_real = (
                    vl_atual_prod_texto + '.' + vl_atual_prod_centavos
            )
            vl_atual_prod_real = float(vl_atual_prod_real)
        else:
            vl_atual_prod_real = float(vl_atual_prod_texto)

        if vl_antigo_prod:
            vl_antigo_prod = vl_antigo_prod.text

            """ 
            As duas linhas abaixo no tratamento de valores antigos
            tem a inteção de corrigir o texto disposto pelo ML
            uma vez que o valor não vem separado do texto
            """
            vl_antigo_prod = (
                vl_antigo_prod[7:vl_antigo_prod.find('reais')].replace('.', '')
            )
            vl_antigo_prod = vl_antigo_prod[:vl_antigo_prod.find('reales')]
            vl_antigo_prod = int(vl_antigo_prod)

            descont_prod = 1 - (vl_atual_prod_real / vl_antigo_prod)
            descont_prod = round(descont_prod, 2)
        else:
            descont_prod = None

        loja_prod = item.find(
            'span', attrs={'class': 'promotion-item__seller'}
        )
        if loja_prod:
            loja_prod = loja_prod.text[4:]

        produto = {
            'link_prod': link_prod,
            'nome_prod': nome_prod,
            'vl_antigo_prod': vl_antigo_prod,
            'vl_atual_prod_real': vl_atual_prod_real,
            'descont_prod': descont_prod,
            'loja_prod': loja_prod,
            'n_pagina_oferta': pagina,
        }
        """
        armazenar as informações de cada produto
         individualmente no dicionário, 
         usando o link do produto como chave.
        """
        produtos[link_prod] = produto

    end_time = time.time()
    execution_time = round(end_time - start_time,2)
    print(
     f'- [LOG]: Página de oferta sofrendo scrapping: {pagina}\n'
     f'- [LOG]: Tempo de execução da função process_page {execution_time}s\n'
    )
    return produtos


def scrapping_mercado_livre_ofertas(paginas=None, producao=False):
    """
    Realiza o scraping de ofertas no site Mercado Livre.

    :param paginas: Número de páginas a serem consultadas.
    Se não informado e producao=True, então paginas=20.
    :type paginas: int, opcional em producao
    :param producao: Indica se está em modo de produção,
    onde o número de páginas pode ser diferente, default é False.
    :type producao: bool, opcional
    :return: None
    """
    start_time = time.time()

    if producao:
        if paginas:
            n = paginas
        else:
            n = 20
    else:
        n = paginas

    with Pool() as pool:
        resultados = pool.map(process_page, range(1, n+1))

    produtos = {}
    for resultado in resultados:
        produtos.update(resultado)

    with open('output/ofertas.json', 'w') as json_file:
        json.dump(list(produtos.values()), json_file)

    print(f'Total de produtos captados: {len(produtos)}')
    end_time = time.time()
    execution_time = round(end_time - start_time,2)
    print(
     f'- [LOG]: Tempo de execução da função principal {execution_time}s\n'
    )

if __name__ == '__main__':
    scrapping_mercado_livre_ofertas(producao=True)
