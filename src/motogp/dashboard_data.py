"""Acesso do dashboard aos dados: lê SOMENTE a camada marts, em modo somente leitura.

A conexão abre apenas o arquivo marts.db, sem anexar as outras camadas. Assim é
fisicamente impossível o dashboard ler a raw ou a refined, ou alterar qualquer dado.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

# Tabelas que o dashboard usa. Qualquer outro nome é recusado.
MARTS_TABLES = (
    "kpi_summary",
    "constructor_wins_by_decade",
    "champion_dominance",
    "top_riders_premier",
    "wins_by_country_decade",
    "podium_lockouts_by_nation",
)


def connect_marts(warehouse_dir: Path) -> sqlite3.Connection:
    """Abre o marts.db em modo somente leitura."""
    marts_db = Path(warehouse_dir) / "marts.db"
    if not marts_db.exists():
        raise FileNotFoundError(
            f"{marts_db} não encontrado. Rode o pipeline antes: "
            "uv run python -m motogp.pipeline"
        )
    return sqlite3.connect(f"{marts_db.resolve().as_uri()}?mode=ro", uri=True)


def read_mart(conn: sqlite3.Connection, table: str) -> pd.DataFrame:
    """Lê uma tabela dos marts exatamente como está, sem nenhum cálculo."""
    if table not in MARTS_TABLES:
        raise ValueError(f"Tabela não permitida no dashboard: {table}")
    return pd.read_sql_query(f'SELECT * FROM "{table}"', conn)


def load_marts(conn: sqlite3.Connection) -> dict[str, pd.DataFrame]:
    """Lê todas as tabelas usadas pelo dashboard."""
    return {table: read_mart(conn, table) for table in MARTS_TABLES}
