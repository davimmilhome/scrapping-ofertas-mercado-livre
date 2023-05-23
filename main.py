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
produtos = []  # Lista de produtos

# Instanciando e definindo configs navegador
options = Options()
options.add_argument('window-size=400,800')  # Seta um tamanho de tela único

prod = 1
if prod == 1:  # Seta configurações de produção
    options.add_argument('--headless')  # Não exibe o navegador

navegador = webdriver.Firefox(options=options)

"""
Bloco Try utilizado abaixo para evitar crash, a saida do navegador será
feita no finally, independete da ocorrencia de erros na execução
"""
try:
    navegador.get('https://www.mercadolivre.com.br/ofertas')
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
                'class': 'andes-money-amount andes-money-amount-combo__previous-value andes-money-amount--previous andes-money-amount--cents-comma', }).text
        vl_antigo_prod.replace('.', '')
        vl_antigo_prod.replace(' ', '')
        limite = vl_antigo_prod.find('reais')
        vl_antigo_prod = vl_antigo_prod[7:limite]
        vl_antigo_prod = int(vl_antigo_prod)

        vl_atual_prod = item.find(
            'span', attrs={'class': 'andes-money-amount__fraction'}).text
        vl_atual_prod = str(vl_atual_prod).replace('.', '')
        vl_atual_prod = int(vl_atual_prod)

        descont_prod = 1 - (vl_atual_prod / vl_antigo_prod)
        descont_prod = round(descont_prod, 2)

        """
        No caso, o link da imagem é gerado juntaemnte com javascript
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

        }
        produtos.append(produto)

    # Saida para o json
    with open('output/ofertas.json', 'w') as json_file:
        json.dump(produtos, json_file)
except:
    raise

finally:
    navegador.quit()

if __name__ == '__main__':
    print(produtos)
    print(f' Total de produtos captados: {len(produtos)}')
