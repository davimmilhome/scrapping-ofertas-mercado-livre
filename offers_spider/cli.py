"""Entrada única. 0 = sucesso, 1 = falha, 2 = coleta parcial."""

import argparse
import logging
import os
import time
from dataclasses import replace
from datetime import datetime, timezone
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
    run_id = None
    run_started = None
    result = None
    run_status = "failed"
    run_error = None
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
            try:
                repository.prune_runs(
                    retention_days=settings.log_retention_days,
                    stale_after_seconds=settings.max_runtime * 2,
                )
            except Exception:
                logger.warning("Não foi possível aplicar a retenção dos logs de execução.")
            run_started = time.monotonic()
            workflow_run_id = os.getenv("GITHUB_RUN_ID")
            workflow_run_attempt = os.getenv("GITHUB_RUN_ATTEMPT")
            run_id = repository.start_run(
                app_env=settings.app_env,
                pages_requested=settings.pages,
                max_duration_seconds=settings.max_runtime,
                workflow_run_id=workflow_run_id,
                workflow_run_attempt=int(workflow_run_attempt)
                if workflow_run_attempt and workflow_run_attempt.isdigit()
                else None,
            )
        stage = "inicialização e coleta no navegador"
        with Browser(settings) as browser:
            result = collect(settings, browser)
        for message in result.failures + result.rejected:
            logger.warning("%s", message)
        if not result.offers:
            logger.error("Nenhuma oferta válida; saída anterior preservada.")
            run_status = "timed_out" if result.timed_out else "failed"
            run_error = result.failures[0] if result.failures else "Nenhuma oferta válida."
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
        run_status = (
            "timed_out" if result.timed_out else ("succeeded" if result.complete else "partial")
        )
        run_error = result.failures[0] if result.failures else None
        return 0 if result.complete else 2
    except Exception as exc:
        logger.error("Falha na etapa %s (%s).", stage, type(exc).__name__)
        run_error = f"{type(exc).__name__}: {str(exc).splitlines()[0][:900]}"
        if stage == "configuração" and isinstance(exc, ValueError):
            logger.error("%s", exc)
        return 1
    finally:
        if repository is not None and run_id is not None:
            finished_at = datetime.now(timezone.utc)
            try:
                repository.finish_run(
                    run_id,
                    status=run_status,
                    finished_at=finished_at,
                    duration_seconds=(time.monotonic() - run_started)
                    if run_started is not None
                    else 0,
                    pages_ok=result.pages_ok if result is not None else 0,
                    offers_found=len(result.offers) if result is not None else 0,
                    failures_count=len(result.failures) if result is not None else 0,
                    rejected_count=len(result.rejected) if result is not None else 0,
                    error_summary=run_error,
                )
            except Exception:
                logger.warning("Não foi possível finalizar o log da execução.")
        if repository is not None:
            repository.close()
