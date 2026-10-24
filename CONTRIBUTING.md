# Contribuindo

## Fluxo de trabalho

O projeto usa GitFlow simplificado:

1. Atualize `develop` localmente.
2. Crie uma branch a partir dela: `feature/nome-curto`, `bugfix/nome-curto`,
   `chore/nome-curto` ou `hotfix/nome-curto`.
3. Faça commits pequenos, com mensagens no padrão Conventional Commits.
4. Execute a suíte local e revise o diff.
5. Abra um Pull Request da branch para `develop`.
6. Aguarde CI verde e revisão quando houver outro revisor disponível; corrija os comentários na mesma branch.
7. Faça merge pelo GitHub. Não faça push direto em `develop`.

`main` recebe apenas PRs de release ou hotfix aprovados. Branches de trabalho
podem ser removidas depois do merge quando não houver necessidade de preservar
o contexto da revisão.

## Ambiente local

```shell
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[dev]"
Copy-Item .env.example .env  # Windows
# cp .env.example .env       # Linux/macOS
```

O padrão é `APP_ENV=development` com SQLite local. Para PostgreSQL, instale
`python -m pip install -e ".[dev,postgres]"` e defina `DATABASE_URL`. Nunca
use credenciais reais no arquivo versionado.

## Validação

```shell
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
git diff --check
```

Os testes padrão não acessam o Mercado Livre. A coleta ao vivo deve ser uma
verificação manual e controlada, usando poucas páginas e respeitando os limites
do site. O teste PostgreSQL é opt-in com `TEST_DATABASE_URL` e deve usar um
banco descartável ou dedicado.

O workflow de segurança executa auditoria de dependências com `pip-audit`,
varredura de segredos com Gitleaks e atualizações semanais via Dependabot.

## Pull Requests

O PR deve explicar:

- problema e comportamento antes/depois;
- alterações de configuração, schema ou contrato JSON;
- impacto de segurança e privacidade;
- comandos de teste executados;
- qualquer limitação de integração ao vivo ou migração manual.

Não incluir no PR dumps de banco, páginas HTML reais com dados desnecessários,
cookies, tokens, credenciais ou logs com URLs sensíveis.

## Reportando vulnerabilidades

Não publique uma vulnerabilidade em issue aberta. Consulte `SECURITY.md` para o
processo de comunicação privada.
