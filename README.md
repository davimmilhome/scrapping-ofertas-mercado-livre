# Scrapping_ml

Esse é um webcrawler que extrai dados da página de ofertas do mercado livre (https://www.mercadolivre.com.br/ofertas). 

## Funcionalidades
No caso, o programa consulta a página de ofertas do mercado livre e estrai os dados definidos no código para um arquivo serializado de dados (JSON).
 
## Como usar

Clone o repositório
Instale as dependências com pip install -r requirements.txt. <br/>
Configure seu webdriver de acordo com o navegador utilizado e a documentação do selenium (no código é utilizado o do Firefox). <br/>
Execute o main.py <br/>
O JSON resultado será exibido no output/

## Tecnologias utilizadas
Python, bibliotecas builtin e third party.

 - BeautifulSoup
 - webdriver

## Contribuindo
Envie um e-mail para davimmilhome@gmail.com com sua intenção de contribuição que podrei avaliar.

## Autores
Davi Martins Milhome.

## Proximos passos
Os próximos passos para esse código são modularizar as buscas, construindo funções próprias para cada find e, após isso, escrever testes automatizados para garantir o funcionamento. <br/>

Além disso, aprimorar a utilização do except para casos específicos.



