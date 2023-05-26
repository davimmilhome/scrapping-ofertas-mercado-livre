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