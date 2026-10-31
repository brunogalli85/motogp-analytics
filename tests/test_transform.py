import pytest

from motogp.transform import build_marts, build_refined, run_sql_folder


@pytest.fixture
def sql_dir(tmp_path):
    """Estrutura sql/refined e sql/marts com consultas inventadas."""
    (tmp_path / "refined").mkdir()
    (tmp_path / "marts").mkdir()
    return tmp_path


def test_camadas_encadeadas_raw_refined_marts(warehouse, sql_dir):
    warehouse.executescript(
        """
        CREATE TABLE raw.results (rider TEXT, points TEXT);
        INSERT INTO raw.results VALUES (' Rossi ', '25'), ('Rossi', '20'), ('Marquez', '');
        """
    )
    (sql_dir / "refined" / "01_results.sql").write_text(
        """
        DROP TABLE IF EXISTS refined.results;
        CREATE TABLE refined.results AS
        SELECT TRIM(rider) AS rider, CAST(NULLIF(points, '') AS INTEGER) AS points
        FROM raw.results;
        """
    )
    (sql_dir / "marts" / "01_pontos.sql").write_text(
        """
        DROP TABLE IF EXISTS marts.pontos;
        CREATE TABLE marts.pontos AS
        SELECT rider, SUM(points) AS total FROM refined.results GROUP BY rider;
        """
    )

    build_refined(warehouse, sql_dir)
    build_marts(warehouse, sql_dir)

    resultado = warehouse.execute("SELECT * FROM marts.pontos ORDER BY rider").fetchall()
    assert resultado == [("Marquez", None), ("Rossi", 45)]


def test_arquivos_rodam_em_ordem_alfabetica(warehouse, sql_dir):
    folder = sql_dir / "refined"
    (folder / "02_b.sql").write_text("CREATE TABLE refined.b AS SELECT x + 1 AS x FROM refined.a;")
    (folder / "01_a.sql").write_text("CREATE TABLE refined.a AS SELECT 1 AS x;")

    executados = run_sql_folder(warehouse, folder)

    assert executados == ["01_a.sql", "02_b.sql"]
    assert warehouse.execute("SELECT x FROM refined.b").fetchone()[0] == 2


def test_pasta_vazia_nao_quebra(warehouse, sql_dir):
    assert run_sql_folder(warehouse, sql_dir / "marts") == []


def test_erro_de_sql_informa_o_arquivo(warehouse, sql_dir):
    (sql_dir / "refined" / "01_ruim.sql").write_text("SELECT * FROM tabela_que_nao_existe;")

    with pytest.raises(RuntimeError, match="01_ruim.sql"):
        build_refined(warehouse, sql_dir)
