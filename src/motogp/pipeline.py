"""Ponto de entrada do pipeline: Kaggle -> raw -> refined -> marts.

Uso:
    python -m motogp.pipeline                   # executa tudo
    python -m motogp.pipeline --skip-download   # usa os CSVs já baixados em data/landing
"""

from __future__ import annotations

import argparse
import logging
import sys

from motogp.config import get_settings
from motogp.db import connect
from motogp.extract import ExtractError, extract
from motogp.logging_config import setup_logging
from motogp.quality import has_blocking_failure, run_checks
from motogp.raw import load_raw
from motogp.transform import build_marts, build_refined

logger = logging.getLogger("motogp.pipeline")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pipeline MotoGP: Kaggle -> raw -> refined -> marts")
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Não baixa do Kaggle; usa os CSVs que já estão em data/landing",
    )
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    settings = get_settings()
    setup_logging(settings.log_level)

    try:
        # 1. Extração: arquivos do Kaggle para data/landing
        if args.skip_download:
            csv_paths = sorted(settings.landing_dir.glob("*.csv"))
            if not csv_paths:
                logger.error("Nenhum CSV em %s. Rode sem --skip-download.", settings.landing_dir)
                return 1
        else:
            csv_paths = extract(settings.kaggle_dataset, settings.landing_dir)

        conn = connect(settings.warehouse_dir)
        try:
            # 2. Raw: cópia fiel dos arquivos
            load_raw(conn, csv_paths)
            # 3. Refined: limpeza, tipos e modelagem (SQL)
            build_refined(conn, settings.sql_dir)
            # 3.1 Qualidade: nenhuma linha pode se perder entre raw e refined
            if has_blocking_failure(run_checks(conn)):
                logger.error("Verificação de qualidade falhou; marts não foram gerados.")
                return 1
            # 4. Marts: indicadores prontos para consumo (SQL)
            build_marts(conn, settings.sql_dir)
        finally:
            conn.close()

    except (ExtractError, RuntimeError) as exc:
        logger.error(exc)
        return 1

    logger.info("Pipeline concluído. Warehouse em %s", settings.warehouse_dir)
    return 0


if __name__ == "__main__":
    sys.exit(run())
