"""Conexão com o warehouse.

Cada camada é um arquivo SQLite separado (raw.db, refined.db, marts.db),
anexado na mesma conexão com o nome da camada. Assim as consultas
escrevem `raw.tabela`, `refined.tabela` e `marts.tabela`, e a separação
entre camadas é física, não só de nome.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

LAYERS = ("raw", "refined", "marts")


def connect(warehouse_dir: Path | None = None) -> sqlite3.Connection:
    """Abre a conexão com as três camadas anexadas.

    Com warehouse_dir=None, tudo fica em memória: é o que os testes usam,
    para nunca abrir o banco real do projeto.
    """
    if warehouse_dir is not None:
        warehouse_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(":memory:")
    for layer in LAYERS:
        target = ":memory:" if warehouse_dir is None else str(warehouse_dir / f"{layer}.db")
        conn.execute(f"ATTACH DATABASE ? AS {layer}", (target,))
    return conn


def list_tables(conn: sqlite3.Connection, layer: str) -> list[str]:
    """Lista as tabelas de uma camada."""
    if layer not in LAYERS:
        raise ValueError(f"Camada desconhecida: {layer}")
    rows = conn.execute(
        f"SELECT name FROM {layer}.sqlite_master WHERE type = 'table' ORDER BY name"
    ).fetchall()
    return [row[0] for row in rows]
