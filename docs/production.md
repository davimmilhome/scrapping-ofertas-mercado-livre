# Operação em produção

Esta aplicação deve rodar como um processo dedicado, sem acesso interativo ao
desktop e sem privilégios administrativos. O navegador precisa ser encerrado
ao fim de cada execução; a coleta deve usar poucas páginas e uma frequência
compatível com os limites do site.

## Segredos e configuração

Defina as variáveis por um gerenciador de segredos do ambiente de execução. No
Worker Cloudflare, use `wrangler secret put DATABASE_URL` e
`wrangler secret put MANUAL_TOKEN`; não coloque credenciais em `.env`
versionado, argumentos da linha de comando, imagens de container ou logs.

```text
DATABASE_URL=postgresql://<usuario>:<senha>@<host>/<banco>?sslmode=require
BASE_URL=https://www.mercadolivre.com.br/ofertas?isSparkleRedirect=true
PAGES=1
PAGE_TIMEOUT_SECONDS=20
RETRIES=2
REQUEST_DELAY_SECONDS=1
MAX_RUNTIME_SECONDS=300
LOG_RETENTION_DAYS=30
```

O arquivo `cloudflare/wrangler.jsonc` mantém os valores operacionais não
secretos. O cron é interpretado em UTC; `17 4 * * *` corresponde a 01:17 em
Brasília. O plano gratuito do Browser Run limita o uso a 10 minutos de
navegador por dia, portanto mantenha uma execução curta e uma página por padrão.
`SCHEMA_BOOTSTRAP=true` deve ser usado apenas na primeira execução; altere para
`false`, faça novo deploy e só então remova a permissão `CREATE` do usuário.

`APP_ENV=production` exige PostgreSQL e HTTPS. Rotacione a senha do banco e os
segredos do ambiente conforme a política da organização.

## Banco e menor privilégio

Use um banco dedicado e um usuário da aplicação sem permissão de superusuário.
Na primeira implantação, `SCHEMA_BOOTSTRAP=true` cria as tabelas e exige
`CREATE` no schema. Depois que a tabela existir, altere a variável para `false`,
faça novo deploy, remova essa permissão e use um usuário separado para futuras
migrações.

```sql
GRANT CONNECT ON DATABASE <banco> TO <usuario_app>;
GRANT USAGE ON SCHEMA public TO <usuario_app>;
GRANT SELECT, INSERT, UPDATE ON TABLE offer_snapshots TO <usuario_app>;
GRANT USAGE, SELECT ON SEQUENCE offer_snapshots_id_seq TO <usuario_app>;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE collection_runs TO <usuario_app>;
```

O tráfego para um PostgreSQL remoto deve usar TLS (`sslmode=require` no mínimo,
ou verificação de certificado conforme a política da organização).

## Backup e restauração

Agende `pg_dump` em armazenamento criptografado, com retenção definida e teste
periódico de restauração. O arquivo de backup não deve ser salvo no workspace
do scraper.

```shell
pg_dump --format=custom --file=offers-$(date +%Y%m%d).dump "$DATABASE_URL"
pg_restore --clean --if-exists --dbname="$RESTORE_DATABASE_URL" offers-YYYYMMDD.dump
```

Registre duração, sucesso, retenção e resultado do último teste de restauração.
Nunca inclua a URL com senha em logs; use a variável injetada pelo secret manager.

## Isolamento do job

- O Worker não tem filesystem persistente; o navegador é fechado no `finally` e
  o job tem limite lógico de 300 segundos.
- Restrinja as chamadas do endpoint manual ao `MANUAL_TOKEN`; o cron não fica
  exposto como endpoint público.
- O navegador deve acessar apenas os domínios necessários para a coleta e não
  usa proxy residencial, stealth, solução de CAPTCHA ou qualquer contorno de
  bloqueio.
- Monitore falhas, tempo de execução, volume de ofertas e crescimento do banco.

## Checklist antes da hospedagem

- Conta Cloudflare com Workers e Browser Run habilitados para o plano escolhido.
- Wrangler autenticado na conta correta, com o nome do Worker revisado antes de
  `npm run deploy`.
- `DATABASE_URL` apontando para o projeto Neon correto, com TLS e usuário
  dedicado; `MANUAL_TOKEN` gerado fora do Git.
- Primeiro deploy com `SCHEMA_BOOTSTRAP=true`, uma execução manual autenticada
  e conferência de `collection_runs` e `offer_snapshots` no Neon.
- Segundo deploy com `SCHEMA_BOOTSTRAP=false`, seguido da remoção de `CREATE` no
  schema e da exclusão do secret legado `NEON_DATABASE_URL` no GitHub.
- Cron conferido em UTC, uma página por execução e orçamento de navegador dentro
  do plano contratado.
- Backup do Neon e restauração de teste definidos antes de considerar o job
  operacional.

As métricas operacionais ficam na tabela `collection_runs`, sem HTML, cookies ou
credenciais. `LOG_RETENTION_DAYS` limita o crescimento dessa tabela e
`MAX_RUNTIME` (Python) ou `MAX_RUNTIME_SECONDS` (Worker) encerra a paginação
quando o orçamento de execução é atingido.
