# Scrapping_ml

Esse é um webcrawler que extrai dados da página de ofertas do mercado livre (https://www.mercadolivre.com.br/ofertas). 

## Funcionalidades
No caso, o programa consulta a página de ofertas do mercado livre e extrai os dados definidos no código para um arquivo serializado de dados (JSON).
 
## Como usar

Clone o repositório
Instale as dependências com pip install -r requirements.txt. <br/>
Configure seu webdriver de acordo com o navegador utilizado e a documentação do selenium (no código é utilizado o do Firefox). <br/>
Execute os teste unitários com o comando  python -m  pytest -v -s -m smoke (garanta que os testes passem), se falharem, indicam que existe algum problema na configuração ou indisponibilidade na url fornecida. <br/>
Execute o main.py <br/>
O JSON resultado será exibido no output/ <br/>
Execute os testes unitários com o comando python -m  pytest -v -s -m output, teste de integridade dos dados. <br/>

## Tecnologias utilizadas
Python, bibliotecas builtin e third party.

 - BeautifulSoup
 - Selenium com webdriver
 - Pytest

## Contribuindo
Envie um e-mail para davimmilhome@gmail.com com sua intenção de contribuição que podrei avaliar.

## Autores
Davi Martins Milhome.

## Proximos passos
Adicionar mais teste, e fazer a exploração de páginas diferentes.



