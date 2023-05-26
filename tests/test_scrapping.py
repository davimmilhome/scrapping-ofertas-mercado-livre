import json
import os

from pytest import mark
from bs4 import BeautifulSoup

import main

@mark.smoke  # Classe smoke utilizada para testes obrigatorios
def test_configuracao_webdriver():
    """
    Testa a configuração do webdriver e a obtenção do conteúdo do site.

    Verifica se a função get_site_content() retorna um objeto
    BeautifulSoup ao obter o conteúdo de um site.
    """
    url = 'https://google.com'
    pagina = ''
    site = main.get_site_content(url, pagina)
    assert isinstance(site, BeautifulSoup)

@mark.smoke # Classe smoke utilizada para testes obrigatorios
def test_disponibilidade_paginas_ML():
    """
     Testa a disponibilidade das páginas de ofertas no Mercado Livre.

    Verifica se a página de ofertas está disponível ao obter o conteúdo
    de uma página específica. O teste verifica se o conteúdo contém um
    elemento <ol> com a classe 'items_container', que é utilizado para
    listar os itens de oferta. Se o elemento for encontrado, considera
    que a página está disponível e contém ofertas.
    """
    url = (
        'https://www.mercadolivre.com.br/ofertas'
        '?container_id=MLB779362-1&page='
    )
    pagina = '1'
    site = main.get_site_content(url, pagina)
    assert site.find('ol', attrs={'class': 'items_container'}) is not None

@mark.output  # Teste de integridade para o arquivo de saída
def test_arquivo_json():
    """
    Testa a integridade do arquivo JSON gerado após a execução do scrapping.

    O teste verifica se o arquivo 'output/ofertas.json' existe e contém dados válidos.
    Caso o arquivo exista, ele é aberto e os seguintes critérios são verificados:

    - Os dados são carregados como uma lista.
    - A lista contém pelo menos um elemento.
    - Cada elemento da lista é um dicionário.
    - Cada dicionário contém as chaves 'link_prod', 'nome_prod',
    'vl_antigo_prod','vl_atual_prod_real', 'descont_prod',
    'loja_prod' e 'n_pagina_oferta'.

    Se o arquivo não existir, o teste falhará e uma mensagem indicando
    a ausência do arquivo será exibida..
    """
    if os.path.exists('output/ofertas.json'):
        with open('output/ofertas.json', 'r') as json_file:
            data = json.load(json_file)
            assert isinstance(data, list)
            assert len(data) > 0
            for produto in data:
                assert isinstance(produto, dict)
                assert 'link_prod' in produto
                assert 'nome_prod' in produto
                assert 'vl_antigo_prod' in produto
                assert 'vl_atual_prod_real' in produto
                assert 'descont_prod' in produto
                assert 'loja_prod' in produto
                assert 'n_pagina_oferta' in produto
    else:
        pytest.fail("[LOG]: Arquivo json não presente no diretorio")

@mark.output  # Teste de integridade para o arquivo de saída
def test_ordem_paginas_oferta():
    """
    Testa se as páginas de oferta no arquivo JSON
    estão em ordem crescente.

    O teste carrega o arquivo 'output/ofertas.json'
    e verifica se para cada oferta, o número da página
    de oferta é igual ou maior que o número da
    página de oferta anterior.
    """
    if os.path.exists('output/ofertas.json'):
        with open('output/ofertas.json', 'r') as json_file:
            data = json.load(json_file)
            assert isinstance(data, list)
            assert len(data) > 0

            # Verifica a ordem das páginas de oferta
            previous_page = None
            for produto in data:
                assert isinstance(produto, dict)
                assert 'n_pagina_oferta' in produto

                current_page = produto['n_pagina_oferta']
                if previous_page is not None:
                    assert current_page >= previous_page

                previous_page = current_page
    else:
        pytest.fail("[LOG]: Arquivo json não presente no diretório")