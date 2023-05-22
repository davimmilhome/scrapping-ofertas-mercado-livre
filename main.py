"""
Docstring inicial
"""
from time import sleep

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

# Instanciando e definindo configs navegador

options = Options()
options.add_argument('window-size=400,800') # Seta um tamanho de tela único para evitar dinamicidade

prod = 1
if prod == 1: # Seta configurações de produção
    options.add_argument('--headless') # Não exibe o navegador

navegador = webdriver.Firefox(options=options)
navegador.get('https://www.mercadolivre.com.br/ofertas')
sleep(1) # Espera a page carregar
page_content = navegador.page_source
site = BeautifulSoup(page_content, 'html.parser') # Convertendo em objeto do bs

#
ofertas_urls = []
ofertas_div = site.findAll('div', attrs={'class': 'promotion-item__container'})

for idx, ofertas_div enumerate(ofertas_div):


if __name__ == '__main__':
    #print(site.prettify()) # exibe o html
    print(ofertas_div)


#navegador.page_source