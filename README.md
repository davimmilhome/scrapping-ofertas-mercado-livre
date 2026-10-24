# Offers Spider

Coleta ofertas públicas do Mercado Livre, exporta JSON e mantém um histórico
diário em SQLite ou PostgreSQL. Python 3.11+ e Chrome ou Firefox instalado.

## Começar

```powershell
git clone https://github.com/davimmilhome/scrapping-ofertas-mercado-livre.git
cd scrapping-ofertas-mercado-livre
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m offers_spider --pages 1
```

No Linux/macOS, ative com `source .venv/bin/activate` e copie o exemplo com
`cp .env.example .env`. Não é necessário configurar um servidor de banco:
SQLite é o padrão. O Selenium Manager localiza/obtém o driver e pode precisar
de internet na primeira execução. `DRIVER_PATH` permite fornecer um driver
compatível já instalado.

Comandos equivalentes: `offers-spider`, `python -m offers_spider` e
`python main.py`.

```shell
python -m offers_spider --pages 3 --json-only
python -m offers_spider --browser firefox --headed
python -m offers_spider --env-file config/local.env --output output/minhas-ofertas.json
python -m offers_spider --help
```

## Configuração

Variáveis de ambiente prevalecem sobre o arquivo `.env`; argumentos da CLI
prevalecem sobre os valores correspondentes. Caminhos relativos são resolvidos
a partir do diretório de execução.

Em `development` e `test`, SQLite é o padrão para desenvolvimento local e testes.
`production` rejeita SQLite e exige uma URL PostgreSQL (`postgresql+psycopg`).

| Variável | Padrão | Uso |
| --- | --- | --- |
| APP_ENV | development | development, test, staging ou production |
| DATABASE_URL | sqlite:///output/offers.sqlite3 | SQLite ou postgresql+psycopg |
| OUTPUT_PATH | output/offers.json | Exportação da execução |
| BASE_URL | https://www.mercadolivre.com.br/ofertas | Página base; filtros existentes são preservados. Em produção, a Action usa a variante `?isSparkleRedirect=true` para reduzir respostas de erro de IPs de datacenter. |
| PAGES | 1 | Páginas de 1 até 100 |
| BROWSER | firefox | chrome ou firefox |
| HEADLESS | true | false para mostrar navegador |
| TIMEOUT | 20 | Limite de navegação e espera por cartões, de 0 a 300 segundos |
| RETRIES | 2 | Tentativas adicionais por página, de 0 a 5 |
| REQUEST_DELAY | 1 | Intervalo entre páginas, de 0 a 60 segundos |
| MAX_RUNTIME | 300 | Limite total da coleta, de 1 a 300 segundos |
| LOG_RETENTION_DAYS | 30 | Dias de retenção dos logs de execução, de 1 a 365 |
| DRIVER_PATH | vazio | Executável chromedriver/geckodriver; não é o executável do navegador |

Para PostgreSQL:

```shell
python -m pip install -e ".[postgres]"
```

Defina `DATABASE_URL=postgresql+psycopg://usuario:senha@localhost/ofertas`.
O banco deve existir; a aplicação cria a tabela. Caracteres especiais da senha
devem ser codificados na URL. Credenciais ficam fora do Git.

## Execução agendada no GitHub Actions com Neon

O workflow [`scraper.yml`](.github/workflows/scraper.yml) executa a coleta
diariamente às 01:17 no horário de Brasília e também pode ser disparado
manualmente. Ele usa o PostgreSQL do Neon como banco persistente; o JSON da
execução fica disponível como artifact por sete dias.

No repositório, crie o secret `NEON_DATABASE_URL` com a URL de conexão do Neon.
Use a URL com o driver `psycopg`, por exemplo:

```text
postgresql://usuario:senha@ep-exemplo.us-east-2.aws.neon.tech/ofertas?sslmode=require
```

Não coloque essa URL em arquivos versionados, logs ou parâmetros de linha de
comando. A primeira execução cria as tabelas `offer_snapshots` e
`collection_runs` automaticamente. `collection_runs` guarda métricas
operacionais (status, duração, páginas, ofertas e falha resumida), sem HTML,
cookies, tokens ou dados pessoais. Registros antigos seguem
`LOG_RETENTION_DAYS`.
Para validar a conexão sem esperar o cron, use **Run workflow** na aba Actions
e acompanhe o artifact e os logs da execução.

## Dados e repetição da coleta

Cada oferta tem identidade extraída do link MLB. Em links de catálogo,
`item_id` tem preferência sobre o ID do catálogo. Sem `item_id`, o registro
representa a página de catálogo, não um vendedor específico. Links sem um ID
reconhecido são rejeitados, em vez de deduplicados por título.

O banco usa a tabela `offer_snapshots`, com chave única
`(marketplace, listing_id, observed_on)`. O dia é calculado em UTC:

- Repetir o anúncio no mesmo dia atualiza o snapshot com a coleta mais recente.
- Uma coleta antiga não sobrescreve uma nova.
- Um novo dia cria outro snapshot.
- Anúncios diferentes com o mesmo título continuam separados.
- Repetições entre páginas da mesma execução mantêm a primeira ocorrência.

Esse modelo registra a última observação diária, não todas as mudanças intradiárias.
IDs internos são gerados pelo banco. Cada lote é uma transação; falhas fazem
rollback e são propagadas.

O JSON contém uma lista, em UTF-8, com este contrato:

```json
{
  "listing_id": "MLB123456789",
  "title": "Fone de ouvido",
  "url": "https://produto.mercadolivre.com.br/MLB-123456789-fone-_JM",
  "price": "999.50",
  "previous_price": "1299.90",
  "seller": "Loja Exemplo",
  "page": 1,
  "collected_at": "2026-01-10T12:00:00+00:00",
  "marketplace": "mercadolivre",
  "discount": "0.2311"
}
```

Valores monetários e desconto são strings decimais para preservar precisão.
O desconto é uma fração: `0.2311` corresponde a 23,11%. Preço anterior,
desconto e vendedor podem ser `null`.

## Falhas e operação

Um navegador é reutilizado durante a execução e encerrado ao final. As páginas
são coletadas sequencialmente, com espera por cartões e tentativas limitadas.
Cartões inválidos são reportados; páginas com falha não impedem as seguintes.
Ausência de cartões reconhecidos é erro, pois pode indicar bloqueio ou mudança
de layout.

| Código de saída | Significado |
| --- | --- |
| 0 | Todas as páginas e cartões reconhecidos processados |
| 1 | Configuração/infraestrutura falhou ou nenhuma oferta válida |
| 2 | Coleta parcial: pelo menos uma página ou cartão falhou |

Os logs no terminal mostram etapa, contagens e rejeições. Em coleta parcial,
as ofertas válidas são persistidas e exportadas em `offers.partial.json`,
preservando `offers.json`. Sem ofertas válidas, arquivos anteriores são
preservados. A escrita do JSON usa substituição atômica.

`MAX_RUNTIME` é verificado antes de cada página e depois de cada carregamento.
Quando atingido, a execução é marcada como `timed_out` e os resultados válidos
são tratados como coleta parcial.

Banco e arquivo não compartilham uma transação: se a exportação falhar depois
do commit, o banco já estará atualizado. A execução retorna 1; repetir a coleta
não duplica os snapshots do dia.

O site pode exigir autenticação, apresentar desafios ou mudar seu HTML.
O programa não contorna esses bloqueios. Use `--headed` para diagnosticar uma
página que não carregou ofertas. Testes offline não garantem a disponibilidade
do site ao vivo.

## Arquitetura

```text
offers_spider/
  cli.py       argumentos, execução e códigos de saída
  config.py    configuração validada
  browser.py   Selenium, espera, tentativas e encerramento
  parser.py    HTML -> ofertas, sem I/O
  domain.py    contrato Offer, Decimal e datas com fuso
  service.py   paginação, falhas parciais e deduplicação do lote
  storage.py   transações SQL e exportação JSON
tests/
  fixtures/    HTML sintético de layouts suportados
```

Não há controllers, CRUD por entidade, pandas ou gerador manual de IDs.
O crawler observa anúncios; ele não tenta inferir um catálogo de produtos
a partir dos títulos. Para ajustar um layout, altere o parser e acrescente
uma fixture com o caso correspondente.

## Desenvolvimento

```shell
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
pre-commit install
```

Os testes padrão não acessam a internet nem abrem navegador. Cobrem preços,
identidade, cartões inválidos, tentativas, encerramento, configuração,
deduplicação, histórico, rollback, exportação e CLI integrada com SQLite.
O GitHub Actions executa testes, lint e formatação em Python 3.11–3.13.

Para integração PostgreSQL, use **um banco de testes dedicado** e defina
`TEST_DATABASE_URL`. O teste prepara a tabela se necessário, insere registros
com uma identidade exclusiva e remove esses registros ao terminar. Sem essa
variável, ele é ignorado. Há um job separado de PostgreSQL na CI.

## Atualização da versão anterior

Consulte [MIGRATION.md](MIGRATION.md) para mudanças no contrato, configuração
e esquema. Nenhum histórico antigo é apagado ou migrado automaticamente.

Consulte também [CONTRIBUTING.md](CONTRIBUTING.md), [AGENTS.md](AGENTS.md) e
[SECURITY.md](SECURITY.md) para o fluxo de contribuição, políticas do repositório
e controles de segurança.

Para operação segura em produção, consulte [docs/production.md](docs/production.md).
