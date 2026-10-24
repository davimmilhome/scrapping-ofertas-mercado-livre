# Políticas do repositório

## Escopo

Estas regras valem para todo o repositório. O objetivo é manter o scraper
reprodutível, seguro e fácil de revisar.

## Arquitetura

- O código de produção fica em `offers_spider/`.
- `domain.py` define o contrato de dados; `parser.py` é puro e não faz I/O.
- `browser.py` é a única camada Selenium.
- `service.py` orquestra paginação e falhas parciais.
- `storage.py` é responsável por SQLAlchemy, transações e JSON.
- Não recriar controllers, CRUD por entidade, estado global ou acesso direto ao
  banco dentro do parser.
- Alterações de layout devem incluir uma fixture HTML e um teste determinístico.

## Ambientes e dados

- `APP_ENV` aceita `development`, `test`, `staging` e `production`.
- Desenvolvimento usa SQLite local por padrão: `sqlite:///output/offers.sqlite3`.
- Testes devem usar SQLite temporário ou `TEST_DATABASE_URL` em banco dedicado.
- Produção exige PostgreSQL; nunca apontar produção para SQLite.
- Produção exige `BASE_URL` HTTPS; limites operacionais são 100 páginas, 300
  segundos, 5 tentativas e 60 segundos de intervalo.
- Arquivos `.env`, bancos, JSONs de saída, logs e credenciais não entram no Git.
- Nunca colocar tokens, senhas, cookies, headers autenticados ou dados pessoais
  em código, testes, fixtures, logs, issues ou PRs.

## GitFlow e commits

- `main` representa releases de produção; `develop` é a integração.
- Criar branches de trabalho a partir de `develop` com prefixos `feature/`,
  `bugfix/`, `hotfix/` ou `chore/`.
- Não fazer commit direto em `main` ou `develop`.
- Usar commits pequenos e descritivos, preferencialmente no formato
  Conventional Commits.
- Toda mudança deve entrar por Pull Request para `develop`.
- O PR precisa descrever comportamento, riscos, migração e validação.
- Só fazer merge com CI verde e revisão concluída. Releases seguem de
  `develop` para `main` por PR separado.

## Qualidade obrigatória

Antes de abrir ou atualizar um PR:

```shell
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
git diff --check
```

O workflow de segurança também executa `pip-audit` e varredura de segredos.

Mudanças no schema ou no contrato de saída também atualizam `README.md`,
`MIGRATION.md` e os testes afetados.

## Coleta responsável

- Não contornar CAPTCHA, autenticação, rate limit ou bloqueios do site.
- Manter espera, tentativas e concorrência configuráveis e conservadoras.
- Não coletar dados pessoais desnecessários.
- Falhas de layout devem ser explícitas; não deduplicar anúncios por título como
  substituto de uma identidade confiável.

## Segurança

Consultar `SECURITY.md` antes de alterar configuração, persistência, CI,
dependências ou coleta. Vulnerabilidades não devem ser publicadas em issues.
