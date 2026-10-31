"""Camadas REFINED e MARTS: executa os arquivos .sql de cada camada, em ordem.

Convenções:
- sql/refined/*.sql leem de raw.*  e criam tabelas refined.*
- sql/marts/*.sql   leem de refined.* e criam tabelas marts.*
- os arquivos rodam em ordem alfabética (use prefixos 01_, 02_, ...)
- cada arquivo começa com DROP TABLE IF EXISTS, para poder rodar de novo
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


def run_sql_folder(conn: sqlite3.Connection, folder: Path) -> list[str]:
    """Executa todos os .sql da pasta e devolve os nomes executados."""
    sql_files = sorted(folder.glob("*.sql"))
    if not sql_files:
        logger.warning("Nenhum arquivo .sql em %s", folder)
        return []

    for sql_file in sql_files:
        logger.info("Executando %s/%s", folder.name, sql_file.name)
        try:
            conn.executescript(sql_file.read_text(encoding="utf-8"))
        except sqlite3.Error as exc:
            raise RuntimeError(f"Erro em {sql_file.name}: {exc}") from exc

    return [f.name for f in sql_files]


def build_refined(conn: sqlite3.Connection, sql_dir: Path) -> list[str]:
    return run_sql_folder(conn, sql_dir / "refined")


def build_marts(conn: sqlite3.Connection, sql_dir: Path) -> list[str]:
    return run_sql_folder(conn, sql_dir / "marts")
