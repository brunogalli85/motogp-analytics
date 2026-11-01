import pytest

from motogp.query import ensure_read_only, format_table, run_query, split_statements


def test_split_statements_ignora_comentarios_e_vazios():
    sql = "-- comentário\nSELECT 1;\n\n-- outro\nSELECT 2;\n"
    assert split_statements(sql) == ["SELECT 1", "SELECT 2"]


@pytest.mark.parametrize("sql", ["DROP TABLE raw.x", "DELETE FROM raw.x", "UPDATE refined.y SET a = 1"])
def test_bloqueia_comandos_que_alteram_dados(sql):
    with pytest.raises(ValueError):
        ensure_read_only(sql)


def test_aceita_select_e_with():
    ensure_read_only("SELECT 1")
    ensure_read_only("WITH x AS (SELECT 1) SELECT * FROM x")


def test_format_table_alinha_colunas_e_mostra_nulo_vazio():
    texto = format_table(["piloto", "vitorias"], [("Rossi", 89), ("Doohan", None)])
    assert texto.splitlines() == [
        "piloto | vitorias",
        "-------+---------",
        "Rossi  | 89      ",
        "Doohan |         ",
    ]


def test_run_query_no_warehouse_em_memoria(warehouse):
    warehouse.execute("CREATE TABLE marts.t AS SELECT 'Ducati' AS fabricante, 2 AS vitorias")
    saida = run_query(warehouse, "SELECT * FROM marts.t")
    assert "Ducati" in saida and saida.endswith("(1 linhas)")
