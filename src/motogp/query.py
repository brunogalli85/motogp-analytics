"""Executa um arquivo .sql de consulta no warehouse e mostra o resultado em tabela.

Uso:
    python -m motogp.query sql/diagnostico/01_categorias.sql

Serve para análises e verificações pontuais. Só aceita consultas de leitura (SELECT/WITH),
para nunca alterar as camadas por engano.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from motogp.config import get_settings
from motogp.db import connect

READ_ONLY_PREFIXES = ("select", "with")


def split_statements(sql: str) -> list[str]:
    """Separa as consultas por ';', ignorando linhas de comentário e trechos vazios."""
    lines = [line for line in sql.splitlines() if not line.strip().startswith("--")]
    return [stmt.strip() for stmt in "\n".join(lines).split(";") if stmt.strip()]


def ensure_read_only(statement: str) -> None:
    if not statement.lower().startswith(READ_ONLY_PREFIXES):
        raise ValueError(f"Só consultas de leitura são permitidas: {statement[:40]}...")


def format_table(columns: list[str], rows: list[tuple]) -> str:
    """Monta uma tabela de texto com colunas alinhadas."""
    cells = [columns] + [["" if v is None else str(v) for v in row] for row in rows]
    widths = [max(len(row[i]) for row in cells) for i in range(len(columns))]
    lines = [" | ".join(value.ljust(w) for value, w in zip(row, widths)) for row in cells]
    lines.insert(1, "-+-".join("-" * w for w in widths))
    return "\n".join(lines)


def run_query(conn: sqlite3.Connection, statement: str) -> str:
    ensure_read_only(statement)
    cursor = conn.execute(statement)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    return f"{format_table(columns, rows)}\n({len(rows)} linhas)"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Executa consultas SQL no warehouse")
    parser.add_argument("sql_file", type=Path)
    args = parser.parse_args(argv)

    conn = connect(get_settings().warehouse_dir)
    try:
        for statement in split_statements(args.sql_file.read_text(encoding="utf-8")):
            print(run_query(conn, statement), end="\n\n")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
