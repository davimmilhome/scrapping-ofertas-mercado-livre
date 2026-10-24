# Runner auto-hospedado

O Mercado Livre bloqueia a navegação originada dos runners públicos do GitHub.
Para manter o GitHub Actions como agendador, o workflow `scraper.yml` usa um
runner auto-hospedado com a etiqueta `offers-spider`. A coleta continua usando
Neon, artefatos, logs, timeout e o mesmo cron.

## Requisitos

- uma máquina ligada no horário da coleta, com rede que consiga abrir
  `https://www.mercadolivre.com.br/ofertas`;
- Windows, Linux ou macOS com Python 3.12, Chrome e acesso de saída HTTPS;
- uma conta de sistema sem privilégios administrativos para o serviço do
  runner;
- o secret `NEON_DATABASE_URL` já configurado no repositório.

## Cadastro

1. No GitHub, abra **Settings → Actions → Runners → New self-hosted runner**.
2. Escolha o sistema operacional da máquina e siga os comandos oficiais de
   download e configuração exibidos pelo GitHub.
3. Durante a configuração, adicione a etiqueta `offers-spider` além das
   etiquetas padrão (`self-hosted`, `Windows`/`Linux`/`macOS`).
4. Instale o runner como serviço e confirme na página de Runners que ele está
   **Idle** e online.

O token exibido pelo GitHub é temporário. Não o coloque no Git, em scripts
versionados, logs ou mensagens. A instalação deve usar um diretório dedicado e
permissões mínimas; não execute o runner como administrador.

## Validação

Depois que o runner estiver online, use **Actions → Scraper → Run workflow** no
branch `develop`. O job deve aparecer com `runs-on: self-hosted, offers-spider`,
executar o navegador local e publicar o snapshot JSON por sete dias. O cron
diário seguirá sendo disparado pelo GitHub.

## Segurança operacional

Este repositório é público. O runner não deve executar workflows de
`pull_request` nem branches não confiáveis e deve ficar em uma máquina isolada,
sem arquivos pessoais. O workflow atual só responde ao cron e ao disparo manual
do repositório; mantenha essa restrição. Atualize o runner, o navegador e o
driver por fontes oficiais e revogue o runner se a máquina for perdida.
