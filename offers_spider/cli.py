"""Entrada única. 0 = sucesso, 1 = falha, 2 = coleta parcial."""

import argparse
import logging
from dataclasses import replace
from pathlib import Path

from .browser import Browser
from .config import Settings
from .service import collect
from .storage import Repository, export_json

logger = logging.getLogger(__name__)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Coleta ofertas do Mercado Livre.")
    parser.add_argument("--env-file", type=Path, help="Arquivo .env; padrão: ./.env")
    parser.add_argument(
        "--app-env",
        choices=["development", "test", "staging", "production"],
        help="Ambiente de execução",
    )
    parser.add_argument("--pages", type=int, help="Número de páginas")
    parser.add_argument("--output", type=Path, help="Destino do JSON")
    parser.add_argument("--browser", choices=["chrome", "firefox"])
    parser.add_argument("--headed", action="store_true", help="Mostrar o navegador")
    parser.add_argument("--json-only", action="store_true", help="Não gravar no banco")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    repository = None
    stage = "configuração"
    try:
        settings = Settings.from_env(args.env_file)
        changes = {}
        for argument, field in (
            ("app_env", "app_env"),
            ("pages", "pages"),
            ("output", "output_path"),
            ("browser", "browser"),
        ):
            value = getattr(args, argument)
            if value is not None:
                changes[field] = value
        if args.headed:
            changes["headless"] = False
        settings = replace(settings, **changes)
        if not args.json_only:
            stage = "conexão e preparação do banco"
            repository = Repository(settings.database_url)
        stage = "inicialização e coleta no navegador"
        with Browser(settings) as browser:
            result = collect(settings, browser)
        for message in result.failures + result.rejected:
            logger.warning("%s", message)
        if not result.offers:
            logger.error("Nenhuma oferta válida; saída anterior preservada.")
            return 1
        if repository:
            stage = "gravação no banco"
            repository.save(result.offers)
        stage = "exportação JSON"
        output = settings.output_path
        if not result.complete:
            output = output.with_name(output.stem + ".partial" + output.suffix)
        export_json(result.offers, output)
        logger.info(
            "Páginas OK: %s/%s; ofertas: %s; páginas com falha: %s; cartões rejeitados: %s; JSON: %s",
            result.pages_ok,
            settings.pages,
            len(result.offers),
            len(result.failures),
            len(result.rejected),
            output,
        )
        return 0 if result.complete else 2
    except Exception as exc:
        logger.error("Falha na etapa %s (%s).", stage, type(exc).__name__)
        if stage == "configuração" and isinstance(exc, ValueError):
            logger.error("%s", exc)
        return 1
    finally:
        if repository is not None:
            repository.close()
