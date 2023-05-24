"""
Este é um web crawler para capturar ofertas de produtos no site Mercado
Livre.

O código utiliza a biblioteca BeautifulSoup e Selenium para fazer a
raspagem de dados do site. Ele acessa a página de ofertas do Mercado
Livre, coleta informações como nome do produto, preço antigo, preço
atual, desconto, link do produto e loja vendedora.

Após a coleta, os dados são armazenados em uma lista de dicionários
chamada 'produtos'. Em seguida, os dados são salvos em um arquivo
JSON no diretório 'output/ofertas.json'.

Instruções de uso:

Certifique-se de ter as bibliotecas BeautifulSoup, Selenium
e demais dependecias instaladas e configuradas, como webdriver.
Execute o código para iniciar o web crawler.
Aguarde a execução do crawler e verifique
o arquivo 'output/ofertas.json' para ver os resultados.

Contribuidores:
Davi Milhome
"""

import json
from time import sleep

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

#  Globals
produtos = [] # Lista de produtos
n = 5 #  Número de páginas de ofertas que serão procuradas

# Instanciando e definindo configs navegador
options = Options()
options.add_argument('window-size=400,800') # Seta um tamanho de tela único

prod = 1
if prod == 1: # Seta configurações de produção
    options.add_argument('--headless') # Não exibe o navegador
    n = 20 #  Número de páginas de ofertas que serão procuradas em produção


def scrapping_mercado_livre_ofertas(paginas):
    """

    :param paginas:
    :return:
    """

    """
    Observe que, o navegador precisa ser adaptado de acordo
    com a necessidade do projeto, nesse caso utiliza-se o
    firefox, porém, será necessário configurar isso em sua 
    máquina específica.
    """


    for pagina in range(1,n +1): #  n+1 pois se trata de fechamento excluso
        print(f'[LOG]: Página de oferta sendo consultada: {pagina}')
        navegador = webdriver.Firefox(options=options)
        """
        Bloco Try utilizado abaixo para evitar crash, a saída do navegador será
        feita no finally, independentemente da ocorrência de erros na execução
        """
        try:
            navegador.get(
            f'https://www.mercadolivre.com.br/ofertas?container_id=MLB779362-1&page={pagina}'
            )
            sleep(1)  # Espera a page carregar
            page_content = navegador.page_source
            site = BeautifulSoup(page_content, 'html.parser')  # Convertendo em bs

            # Setando elementos BS
            ofertas_ol = site.find('ol', attrs={'class': 'items_container'})
            """
            O código abaixo está captado todos os itens da lista (li).
            Quando eu fiz pela primeira vez, estava selecionando por uma class
            especifica, porém, essas classes são dinamicas.
            """
            ofertas_li = ofertas_ol.findAll('li')

            for idx, item in enumerate(ofertas_li):

                link_prod = item.find(
                    'a', attrs={'class': 'promotion-item__link-container'})['href']

                nome_prod = item.find(
                    'p', attrs={'class': 'promotion-item__title'}).text

                """
                O elemento abaixo vem no formato > Antes: 1165 reaisR$1.165 < para 
                um prod qualquer, sendo assim, precisa do tratamento utilizado
                """
                vl_antigo_prod = item.find(
                    's',
                    attrs={
                        'class': 'andes-money-amount andes-money-amount-combo__previous-value andes-money-amount--previous andes-money-amount--cents-comma', })
                vl_atual_prod = item.find(
                    'span', attrs={'class': 'andes-money-amount__fraction'}).text
                vl_atual_prod = str(vl_atual_prod).replace('.', '')
                vl_atual_prod = int(vl_atual_prod)

                if vl_antigo_prod:
                    vl_antigo_prod = vl_antigo_prod.text
                    vl_antigo_prod.replace('.', '')
                    vl_antigo_prod.replace(' ', '')
                    limite = vl_antigo_prod.find('reais')
                    vl_antigo_prod = vl_antigo_prod[7:limite]
                    vl_antigo_prod = int(vl_antigo_prod)
                    descont_prod = 1 - (vl_atual_prod / vl_antigo_prod)
                    descont_prod = round(descont_prod, 2)
                else:
                    descont_prod = None


                """
                No caso, o link da imagem é gerado juntamente com javascript
                de forma assíncrona, então, quando a requisição é feita,
                nem sempre a url da imagem é oferecida, mas sim uma URI
                para ser feita a busca da imagem em uma fonte externa,
                dessa forma, captar o link da imagem pode não ser 
                interessante
                """
                # link_img_prod = item.find(
                #    'img', attrs={'class': 'promotion-item__img'})['src']

                # O texto de produto da loja é > por nome da loja

                loja_prod = item.find(
                    'span', attrs={'class': 'promotion-item__seller'})
                if loja_prod != None:
                    loja_prod = loja_prod.text
                    loja_prod = loja_prod[4:]  # Tratamento para retirar 'por'

                prazo_frete_prod = item.find(
                    'span', attrs={'class': 'promotion-item__seller'})

                produto = {
                    'link_prod': link_prod,
                    'nome_prod': nome_prod,
                    'vl_antigo_prod': vl_antigo_prod,
                    'vl_atual_prod': vl_atual_prod,
                    'descont_prod': descont_prod,
                    # 'link_img_prod' : link_img_prod,
                    'loja_prod': loja_prod,
                    'n_pagina_oferta' : pagina, # Número da página da oferta

                }
                produtos.append(produto)

            #  Saida para o json, no caso o pagina é o n° da iteração
            #  Ou seja, é o número da página de oferta  especifica

            with open(f'output/ofertas.json', 'w') as json_file:
                json.dump(produtos, json_file)

        finally:
            navegador.quit()



if __name__ == '__main__':
    scrapping_mercado_livre_ofertas(n) # Instanciando a função
    print(f' Total de produtos captados: {len(produtos)}')
