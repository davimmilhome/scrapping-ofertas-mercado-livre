# Segurança

## Modelo de ameaça

O projeto abre páginas de terceiros, executa um navegador local, grava preços e
URLs em banco e pode receber uma URL de PostgreSQL com credenciais. Os riscos
principais são vazamento de segredo, execução com configuração de produção no
ambiente errado, persistência corrompida, dependências vulneráveis e bloqueio
ou abuso do site coletado.

## Controles atuais

- `.env`, bancos, logs e saídas estão no `.gitignore`.
- `APP_ENV=production` rejeita SQLite para evitar um banco local acidental em
  produção.
- Senhas de banco não são incluídas nas mensagens de erro do CLI; SQLAlchemy
  usa `hide_parameters=True`.
- Parser valida esquemas HTTP(S), identidade do anúncio e valores monetários.
- Escrita JSON é atômica; gravações SQL usam transação e rollback.
- Dependências são fixadas por faixas e verificadas na CI com testes e Ruff.
- O workflow do GitHub Actions usa `permissions: contents: read`.
- A CI cancela execuções antigas, impõe timeout nos jobs e valida limites de
  configuração antes de iniciar o navegador.
- A CI executa `pip-audit` e Gitleaks; Dependabot acompanha Python e Actions.
- O scraper não resolve CAPTCHA nem tenta contornar autenticação, rate limit ou
  bloqueios.

## Regras operacionais

- Nunca commitar `.env`, credenciais, cookies, tokens, dumps ou páginas reais
  contendo dados pessoais.
- Use um usuário de banco dedicado e com o menor privilégio necessário.
- Use PostgreSQL em produção com TLS quando o banco estiver fora da máquina.
- Não reutilize `TEST_DATABASE_URL` em staging ou produção.
- Não execute migrações destrutivas sem backup e revisão.
- Mantenha o navegador e os drivers atualizados; prefira Selenium Manager ou
  binários obtidos de fontes oficiais.
- Restrinja permissões do diretório de saída e do arquivo SQLite em máquinas
  compartilhadas.
- A coleta deve permanecer em baixa frequência e respeitar os termos e limites
  do site.

## Controles de produção

As instruções executáveis de deploy, menor privilégio, TLS, backup, restauração
e isolamento estão em [docs/production.md](docs/production.md). O GitHub já está
protegido em `develop` e `main` com:

- PR obrigatório; revisão humana é recomendada quando houver outro mantenedor disponível;
- checks `test (3.11)`, `test (3.12)`, `test (3.13)`, `dependency-audit` e
  `secret-scan`;
- resolução de conversas e proibição de bypass, force push e exclusão.

Ainda é necessário aplicar no ambiente de execução:

- um gerenciador de segredos, PostgreSQL com TLS, backups e testes de restauração;
- usuário de sistema sem privilégios e limites de CPU, memória e tempo.

## Relato privado

Use o [GitHub Security Advisory privado](https://github.com/davimmilhome/scrapping-ofertas-mercado-livre/security/advisories/new)
quando estiver habilitado. Se o GitHub não apresentar esse formulário, envie
uma mensagem privada ao mantenedor antes de abrir uma issue pública. Inclua
impacto, passos de reprodução mínimos, versão/commit afetado e uma correção
sugerida, sem anexar segredos reais.
