import pytest

from motogp.raw import load_csv, load_raw, table_name_for


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("riders.csv", "riders"),
        ("Riders Info.csv", "riders_info"),
        ("grandPrixWinners.csv", "grand_prix_winners"),
        ("constructure-world-championship.csv", "constructure_world_championship"),
    ],
)
def test_table_name_for(tmp_path, filename, expected):
    assert table_name_for(tmp_path / filename) == expected


def test_raw_mantem_nomes_de_colunas_originais(warehouse, write_csv):
    csv = write_csv("riders.csv", "Rider Name,Wins\nValentino Rossi,89\n")

    load_csv(warehouse, csv)

    cursor = warehouse.execute("SELECT * FROM raw.riders")
    assert [d[0] for d in cursor.description] == ["Rider Name", "Wins"]


def test_raw_nao_altera_nenhum_valor(warehouse, write_csv):
    """Espaços, zeros à esquerda, vazios e 'N/A' chegam intactos."""
    csv = write_csv("results.csv", "number,team,points\n007, Ducati ,\n46,N/A,25\n")

    load_csv(warehouse, csv)

    rows = warehouse.execute("SELECT * FROM raw.results").fetchall()
    assert rows == [("007", " Ducati ", ""), ("46", "N/A", "25")]


def test_raw_grava_tudo_como_texto(warehouse, write_csv):
    csv = write_csv("results.csv", "points\n25\n")

    load_csv(warehouse, csv)

    tipo = warehouse.execute("SELECT typeof(points) FROM raw.results").fetchone()[0]
    assert tipo == "text"


def test_raw_le_arquivo_em_latin1(warehouse, write_csv):
    csv = write_csv("riders.csv", "nome\nÁlex Márquez\n", encoding="latin-1")

    load_csv(warehouse, csv)

    assert warehouse.execute("SELECT nome FROM raw.riders").fetchone()[0] == "Álex Márquez"


def test_raw_rodar_duas_vezes_nao_duplica(warehouse, write_csv):
    csv = write_csv("riders.csv", "nome\nRossi\nMarquez\n")

    load_raw(warehouse, [csv])
    summary = load_raw(warehouse, [csv])

    assert summary == {"riders": 2}
    assert warehouse.execute("SELECT COUNT(*) FROM raw.riders").fetchone()[0] == 2
