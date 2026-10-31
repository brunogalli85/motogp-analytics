import pytest

from motogp.db import LAYERS, connect, list_tables


def test_conexao_em_memoria_tem_as_tres_camadas(warehouse):
    schemas = {row[1] for row in warehouse.execute("PRAGMA database_list")}
    assert set(LAYERS) <= schemas


def test_cada_camada_vira_um_arquivo_separado(tmp_path):
    conn = connect(tmp_path)
    conn.close()

    assert sorted(p.name for p in tmp_path.glob("*.db")) == ["marts.db", "raw.db", "refined.db"]


def test_list_tables_por_camada(warehouse):
    warehouse.execute("CREATE TABLE raw.a (x TEXT)")
    warehouse.execute("CREATE TABLE refined.b (x TEXT)")

    assert list_tables(warehouse, "raw") == ["a"]
    assert list_tables(warehouse, "refined") == ["b"]
    assert list_tables(warehouse, "marts") == []


def test_list_tables_rejeita_camada_desconhecida(warehouse):
    with pytest.raises(ValueError):
        list_tables(warehouse, "gold")
