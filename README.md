# scrapping-offers

Esse é um webcrawler que extrai dados de páginas de ofertas 

Marketplaces incluídos: </br>
Mercado Livre [página de ofertas] - (https://www.mercadolivre.com.br/ofertas). <br/>


## Como usar

Clone o repositório
Instale as dependências com pip install -r requirements.txt. <br/>
Crie um .env com base em .env.example </br> <br/>
Configure seu webdriver de acordo com o navegador utilizado e a documentação do selenium (https://selenium-python.readthedocs.io/installation.html). </br> </br>


O JSON resultado será exibido no diretório output/, com a seguinte estrutura: <br/> <br/>

        product = {
            'product_link': str,
            'product_name': str,
            'previous_value': num,
            'actual_value': num,
            'discount': float,
            'store': str,
            'number_of_offer_page': int,
            'market_place': str,
            'timestamp': str,
        }
        

## Tecnologias utilizadas
Python, bibliotecas builtin e third party.

## Contribuindo
Envie um e-mail para davimmilhome@gmail.com com sua intenção de contribuição que poderei avaliar.

## Autores
Davi Martins Milhome.

## Proximos passos
Adicionar mais teste, e fazer a exploração de páginas diferentes.



