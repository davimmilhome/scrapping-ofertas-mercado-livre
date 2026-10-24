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

## Pendências recomendadas

1. Adicionar `pip-audit` ou Dependabot à CI para alertas de dependências.
2. Adicionar varredura de segredos (por exemplo, Gitleaks) antes do merge.
3. Configurar branch protection, revisão obrigatória e checks obrigatórios em
   `develop` e `main`.
4. Usar um gerenciador de segredos no deploy; nunca passar credenciais via CLI.
5. Definir backup, retenção e restauração do PostgreSQL antes de produção.
6. Avaliar isolamento do navegador e limites de CPU, memória e tempo em jobs
   automatizados.

## Relato privado

Como o repositório não possui um canal privado de segurança configurado, envie
um relato privado ao mantenedor antes de abrir uma issue pública. Inclua impacto,
passos de reprodução mínimos, versão/commit afetado e uma correção sugerida,
sem anexar segredos reais.
