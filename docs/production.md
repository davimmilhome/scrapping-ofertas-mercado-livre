# Operação em produção

Esta aplicação deve rodar como um processo dedicado, sem acesso interativo ao
desktop e sem privilégios administrativos. O navegador precisa ser encerrado
ao fim de cada execução; a coleta deve usar poucas páginas e uma frequência
compatível com os limites do site.

## Segredos e configuração

Defina as variáveis por um gerenciador de segredos do ambiente de execução
(por exemplo, GitHub Actions Secrets/Environments, Vault ou o secret manager do
provedor de nuvem). No workflow do GitHub Actions, o nome esperado é
`NEON_DATABASE_URL`, contendo uma URL PostgreSQL do Neon. Não coloque
credenciais em `.env` versionado, argumentos da linha de comando, imagens de
container ou logs.

```text
APP_ENV=production
DATABASE_URL=postgresql://<usuario>:<senha>@<host>/<banco>?sslmode=require
BASE_URL=https://www.mercadolivre.com.br/ofertas?isSparkleRedirect=true
HEADLESS=true
PAGES=1
TIMEOUT=20
RETRIES=2
REQUEST_DELAY=1
```

`APP_ENV=production` exige PostgreSQL e HTTPS. Rotacione a senha do banco e os
segredos do ambiente conforme a política da organização.

## Banco e menor privilégio

Use um banco dedicado e um usuário da aplicação sem permissão de superusuário.
Como a versão atual cria a tabela na inicialização, o bootstrap pode conceder
`CREATE` no schema; depois que a tabela existir, remova essa permissão e use um
usuário separado para futuras migrações.

```sql
GRANT CONNECT ON DATABASE <banco> TO <usuario_app>;
GRANT USAGE ON SCHEMA public TO <usuario_app>;
GRANT SELECT, INSERT, UPDATE ON TABLE offer_snapshots TO <usuario_app>;
GRANT USAGE, SELECT ON SEQUENCE offer_snapshots_id_seq TO <usuario_app>;
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

- Execute com usuário do sistema sem privilégios e filesystem de saída dedicado.
- Aplique timeout do orquestrador maior que o limite de uma execução e encerre
  processos Selenium órfãos.
- Restrinja egress quando possível; o navegador deve acessar apenas os domínios
  necessários para a coleta.
- Monitore falhas, tempo de execução, volume de ofertas e crescimento do banco.
