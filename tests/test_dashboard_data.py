"""Testes do acesso do dashboard aos dados.

Usam um marts.db inventado numa pasta temporária, nunca o banco do projeto.
"""

import re
import sqlite3
from pathlib import Path

import pytest

from motogp.dashboard_data import MARTS_TABLES, connect_marts, load_marts, read_mart

PROJECT = Path(__file__).resolve().parents[1]


@pytest.fixture
def warehouse_dir(tmp_path):
    """Pasta com um marts.db inventado contendo todas as tabelas do dashboard."""
    with sqlite3.connect(tmp_path / "marts.db") as conn:
        for table in MARTS_TABLES:
            conn.execute(f"CREATE TABLE {table} (season INTEGER, valor REAL)")
        conn.execute("INSERT INTO champion_dominance VALUES (2022, 66.7)")
    return tmp_path


def test_le_tabela_dos_marts_sem_alterar_valores(warehouse_dir):
    conn = connect_marts(warehouse_dir)
    df = read_mart(conn, "champion_dominance")
    conn.close()

    assert df.to_dict("records") == [{"season": 2022, "valor": 66.7}]


def test_load_marts_traz_todas_as_tabelas(warehouse_dir):
    conn = connect_marts(warehouse_dir)
    marts = load_marts(conn)
    conn.close()

    assert set(marts) == set(MARTS_TABLES)


def test_conexao_e_somente_leitura(warehouse_dir):
    conn = connect_marts(warehouse_dir)
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        conn.execute("INSERT INTO champion_dominance VALUES (2023, 50.0)")
    conn.close()


def test_recusa_tabela_fora_da_lista(warehouse_dir):
    conn = connect_marts(warehouse_dir)
    with pytest.raises(ValueError):
        read_mart(conn, "race_wins")
    conn.close()


def test_sem_marts_db_da_mensagem_clara(tmp_path):
    with pytest.raises(FileNotFoundError, match="Rode o pipeline"):
        connect_marts(tmp_path)


def test_conexao_nao_enxerga_outras_camadas(warehouse_dir):
    (warehouse_dir / "raw.db").touch()
    conn = connect_marts(warehouse_dir)
    bancos = {row[1] for row in conn.execute("PRAGMA database_list")}
    conn.close()

    assert bancos == {"main"}


@pytest.mark.parametrize(
    "arquivo", ["dashboard/app.py", "src/motogp/dashboard_data.py"], ids=lambda p: p
)
def test_dashboard_nao_cita_raw_nem_refined(arquivo):
    texto = (PROJECT / arquivo).read_text(encoding="utf-8")
    assert not re.search(r"\b(raw|refined)\.", texto)
