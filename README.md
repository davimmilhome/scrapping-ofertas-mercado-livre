# Scrapping_ml

Esse é um webcrawler que extrai dados da página de ofertas do mercado livre (https://www.mercadolivre.com.br/ofertas). <br/>


## Como usar

Clone o repositório
Instale as dependências com pip install -r requirements.txt. <br/> <br/>
Configure seu webdriver de acordo com o navegador utilizado e a documentação do selenium (https://selenium-python.readthedocs.io/installation.html). No código é utilizado o webdriver do Firefox, essa config precisa ser adaptada de acordo com a sua realidade. <br/> <br/>
Execute os teste unitários com o comando  python -m  pytest -v -s -m smoke (garanta que os testes passem), se falharem, indicam que existe algum problema na configuração ou indisponibilidade na url fornecida. <br/> <br/>
Execute o main.py <br/> <br/>
O JSON resultado será exibido no diretório output/, com a seguinte estrutura: <br/> <br/>

        produto = {
            'link_prod': str,
            'nome_prod': str,
            'vl_antigo_prod': num,
            'vl_atual_prod_real': num,
            'descont_prod': float,
            'loja_prod': str,
            'n_pagina_oferta': int,
        }
        
Execute os testes unitários com o comando python -m  pytest -v -s -m output, teste de integridade dos dados. <br/> <br/>

## Tecnologias utilizadas
Python, bibliotecas builtin e third party.

## Contribuindo
Envie um e-mail para davimmilhome@gmail.com com sua intenção de contribuição que poderei avaliar.

## Autores
Davi Martins Milhome.

## Proximos passos
Adicionar mais teste, e fazer a exploração de páginas diferentes.



