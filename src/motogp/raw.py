"""Camada RAW: copia cada CSV para uma tabela, sem alterar nada.

Regras desta camada:
- nomes de colunas iguais aos do arquivo;
- todos os valores gravados como texto, exatamente como estão no CSV
  (vazio continua vazio, "N/A" continua "N/A", "007" continua "007");
- nenhuma limpeza, conversão de tipo ou remoção de linhas.

Toda transformação acontece na camada refined.
"""

from __future__ import annotations

import csv
import logging
import re
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


def table_name_for(csv_path: Path) -> str:
    """Nome da tabela a partir do nome do arquivo: 'Riders Info.csv' -> 'riders_info'.

    Só o NOME da tabela é padronizado; o conteúdo do arquivo não muda.
    """
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", csv_path.stem.strip())
    name = re.sub(r"[^0-9a-zA-Z]+", "_", name)
    return name.strip("_").lower()


def quote_identifier(name: str) -> str:
    """Coloca o identificador entre aspas, para aceitar espaços e acentos."""
    return '"' + name.replace('"', '""') + '"'


def read_csv_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    """Lê cabeçalho e linhas como texto puro. Tenta UTF-8 e depois latin-1."""
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            with path.open(newline="", encoding=encoding) as file:
                reader = csv.reader(file)
                header = next(reader)
                rows = list(reader)
            if encoding != "utf-8-sig":
                logger.warning("%s não está em UTF-8; lido como %s", path.name, encoding)
            return header, rows
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Não foi possível ler {path.name}")  # pragma: no cover


def load_csv(conn: sqlite3.Connection, csv_path: Path) -> tuple[str, int]:
    """Recria raw.<tabela> com o conteúdo do CSV. Rodar de novo não duplica dados."""
    table = table_name_for(csv_path)
    header, rows = read_csv_rows(csv_path)

    columns = ", ".join(f"{quote_identifier(col)} TEXT" for col in header)
    placeholders = ", ".join("?" for _ in header)
    target = f"raw.{quote_identifier(table)}"

    with conn:  # transação: ou grava tudo, ou nada
        conn.execute(f"DROP TABLE IF EXISTS {target}")
        conn.execute(f"CREATE TABLE {target} ({columns})")
        conn.executemany(f"INSERT INTO {target} VALUES ({placeholders})", rows)

    logger.info("raw.%-30s %7d linhas | %2d colunas", table, len(rows), len(header))
    return table, len(rows)


def load_raw(conn: sqlite3.Connection, csv_paths: list[Path]) -> dict[str, int]:
    """Carrega todos os CSVs na camada raw."""
    return dict(load_csv(conn, path) for path in csv_paths)
