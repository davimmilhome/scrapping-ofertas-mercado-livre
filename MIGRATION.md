# Migração para 0.2

## Código e execução

O pacote `offers_spider` substitui `cfg`, `controllers`, `database`,
`parsers`, `scrappers` e `utils`. A compatibilidade de execução por
`python main.py` permanece; imports das classes antigas foram removidos.
Recrie o ambiente virtual e instale com `python -m pip install -e .`.

Não há dependência de pandas/numpy, chromedriver-autoinstaller ou psycopg2.
O suporte opcional a PostgreSQL usa psycopg 3.

## Configuração

Substitua `cfg/cfg.env` e as variáveis `DB_1_*` por `DATABASE_URL` no
`.env` (ou arquivo selecionado por `--env-file`).
`TYPE_OF_DRIVER` passa a ser `BROWSER=chrome|firefox`.
`DOWNLOAD_PATH` passa a ser `OUTPUT_PATH`.
`DRIVER_PATH` é opcional e sempre se refere ao driver, inclusive no Firefox.

## Banco

A tabela nova é `offer_snapshots`. As tabelas antigas `product`, `store`,
`marketplace` e `offers` não são alteradas. Faça backup antes de qualquer
importação histórica e mantenha-as até validar os resultados.

Não há migração automática: o esquema anterior não oferece uma identidade
confiável de anúncio nem define o fuso dos timestamps. Importar silenciosamente
poderia colapsar ofertas distintas ou atribuir observações ao dia errado.

Para migrar um histórico existente:

1. Exporte `offers` com o nome da loja relacionado.
2. Extraia a identidade de `link_offer` usando `listing_identity()`.
   Separe para revisão links sem identidade e relações órfãs.
3. Determine o fuso usado pelas datas antigas antes de convertê-las para UTC.
4. Construa objetos `Offer` com preços `Decimal`, campos abaixo e data com fuso.
5. Grave com `Repository.save()` em um banco novo e confira contagens, dias,
   preços e anúncios. Múltiplas observações do mesmo dia serão consolidadas.

| Campo antigo | Campo novo |
| --- | --- |
| link_offer | url e listing_id extraído da URL |
| name_product / title_offer | title |
| value_offer | price |
| previous_value | previous_price |
| name_store / loja relacionada | seller |
| number_of_offer_page | page |
| date_time_offer | collected_at com fuso explícito |
| id_makertplace / FK de marketplace | marketplace = mercadolivre |
| discount_offer_decimals | discount recalculado |

## JSON e consumidores

O nome padrão continua `output/offers.json`. O conteúdo usa o contrato
documentado no README. Preços passam a strings decimais e timestamps incluem
UTC. Atualize dashboards e integrações que esperavam floats ou nomes antigos.
Coletas parciais escrevem `offers.partial.json` e retornam código 2.

## Branches

A refatoração foi baseada no commit `62d4c48` da branch padrão `develop`.
A comparação com `main` mostrou que seu único commit exclusivo é um merge,
sem alterações exclusivas de arquivos. A refatoração permanece em uma branch
local para revisão; nenhuma branch remota foi atualizada.
