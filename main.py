"""
Docstring inicial
"""
import json
from time import sleep

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

# Globals

produtos = [] # Lista de produtos

# Instanciando e definindo configs navegador
options = Options()
options.add_argument('window-size=400,800') # Seta um tamanho de tela único

prod = 1
if prod == 1: # Seta configurações de produção
    options.add_argument('--headless') # Não exibe o navegador

navegador = webdriver.Firefox(options=options)
navegador.get('https://www.mercadolivre.com.br/ofertas')
sleep(1) # Espera a page carregar
page_content = navegador.page_source
site = BeautifulSoup(page_content, 'html.parser') # Convertendo em bs

# Setando elementos BS

ofertas_ol = site.find('ol', attrs={'class': 'items_container'})
ofertas_li = ofertas_ol.findAll('li', attrs={'class': 'promotion-item sup'})

for idx, item in enumerate(ofertas_li):

    link_prod = item.find(
        'a', attrs={'class': 'promotion-item__link-container'})['href']
    nome_prod = item.find(
        'p', attrs={'class': 'promotion-item__title'}).text
    vl_antigo_prod = item.find(
        'span', attrs={'class': 'andes-money-amount__fraction'}).text.replace('.','')
    # vl_atual_prod =
    # descont_prod
    # link_img_prod
    # prazo_frete_prod
    # loja_prod =

    produto = {
        'link_prod' : link_prod,
        'nome_prod' : nome_prod,
        'vl_antigo_prod' : vl_antigo_prod,
    }
    produtos.append(produto)


if __name__ == '__main__':
    print(produtos)
    #print(site.prettify()) # exibe o html
    #print(ofertas_ol)
    #print(ofertas_li)

