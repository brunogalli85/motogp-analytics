"""Testes do SQL da camada refined.

Monta uma camada raw inventada, com os mesmos nomes de colunas do dataset real
(inclusive espaços sobrando, símbolo ™ e vazios), roda os arquivos de sql/refined
do projeto e confere o resultado. Tudo em memória: o banco real nunca é aberto.
"""

from pathlib import Path

import pytest

from motogp.transform import build_refined

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"

RAW_TABLES = {
    "grand_prix_race_winners": (
        ["Circuit", "Class", "Constructor", "Country", "Rider", "Season"],
        [
            ("Mugello", "MotoGP™", "Ducati", "IT", "Pecco Bagnaia", "2022"),
            ("Assen", "MotoGP™", " Ducati ", "IT", " Pecco Bagnaia", "2022"),
            ("Assen", "Moto2™", "Kalex", "ES", "Augusto Fernandez", "2022"),
            ("Assen", "500cc", "Honda", "AU", "Mick Doohan", "1998"),
            ("Assen", "125cc", "Honda", "IT", "Valentino Rossi", "1996"),
            ("Mugello", "500cc", "Honda", "it", "Valentino Rossi", "2001"),
            # campos em branco, como acontece no dataset real
            ("Monza", "350cc", "MV Agusta", "", "  ", "1955"),
            ("Monza", "250cc", "", "IT", "Valentino Rossi", "1999"),
        ],
    ),
    "riders_finishing_positions": (
        ["Rider", "Victories", "NumberofSecond", "NumberofThird",
         "Numberof4th", "Numberof5th", "Numberof6th", "Country"],
        [
            ("Valentino Rossi", "115", "52", "47", "38", "30", "21", "IT"),
            ("Pecco Bagnaia", "28", "20", "15", "10", "8", ""),
            ("Mick Doohan", "54", "31", "10", "", "", "", "AU"),
            ("Loris Capirossi", "29", "30", "40", "20", "15", "10", "IT"),
            # repetidos, como no dataset real
            ("Loris Capirossi", "29", "30", "40", "20", "15", "10", "IT"),  # linha idêntica
            ("Nello Pagani", "3", "1", "0", "0", "0", "0", "IT"),
            ("Nello Pagani", "2", "1", "1", "", "", "", "GB"),            # estatística dividida
        ],
    ),
    "constructure_world_championship": (
        ["Season", "Constructor", "Class"],
        [
            ("2022", "Ducati", "MotoGP™"),
            ("2022", "Kalex", "Moto2™"),
            ("1960", "MV Agusta", "500cc"),
        ],
    ),
    "grand_prix_events_held": (
        ["Times", "Track", "Country"],
        [("280", "TT Circuit Assen", "NL"), ("60", " Mugello ", "it")],
    ),
    "same_nation_podium_lockouts": (
        ["Season", "Track", "Riders` Nation", "Class"],
        [("2022", "Termas de Río Hondo", "ES", "MotoGP™"), ("2021", "Misano", "IT", "MotoE™")],
    ),
}


@pytest.fixture
def refined(warehouse):
    """Warehouse com a raw inventada e a refined já construída."""
    for table, (columns, rows) in RAW_TABLES.items():
        cols = ", ".join(f'"{c}" TEXT' for c in columns)
        warehouse.execute(f"CREATE TABLE raw.{table} ({cols})")
        # completa linhas mais curtas com vazio, como acontece em CSVs reais
        padded = [tuple(row) + ("",) * (len(columns) - len(row)) for row in rows]
        marks = ", ".join("?" for _ in columns)
        warehouse.executemany(f"INSERT INTO raw.{table} VALUES ({marks})", padded)

    build_refined(warehouse, SQL_DIR)
    return warehouse


def scalar(conn, sql):
    return conn.execute(sql).fetchone()[0]


# --- dimensões -------------------------------------------------------------

def test_riders_um_por_nome_sem_espacos(refined):
    nomes = [r[0] for r in refined.execute("SELECT rider_name FROM refined.riders ORDER BY 1")]
    assert nomes == [
        "Augusto Fernandez", "Desconhecido", "Loris Capirossi", "Mick Doohan", "Nello Pagani",
        "Pecco Bagnaia", "Valentino Rossi",
    ]


def test_riders_pais_da_vitoria_mais_recente_em_maiusculas(refined):
    pais = scalar(refined, "SELECT country_code FROM refined.riders WHERE rider_name = 'Valentino Rossi'")
    assert pais == "IT"  # a vitória de 2001 veio como 'it'


def test_constructors_sem_duplicar_por_espaco(refined):
    nomes = [r[0] for r in refined.execute("SELECT constructor_name FROM refined.constructors ORDER BY 1")]
    assert nomes == ["Desconhecido", "Ducati", "Honda", "Kalex", "MV Agusta"]


def test_circuits_tipados(refined):
    linha = refined.execute(
        "SELECT circuit_name, country_code, gp_events_held FROM refined.circuits WHERE circuit_name = 'Mugello'"
    ).fetchone()
    assert linha == ("Mugello", "IT", 60)


# --- fato race_wins --------------------------------------------------------

def test_race_wins_mantem_todas_as_vitorias(refined):
    """Nenhuma vitória some no JOIN, nem as que têm campos em branco."""
    assert scalar(refined, "SELECT COUNT(*) FROM refined.race_wins") == 8


def test_race_wins_remove_simbolo_tm(refined):
    classes = {r[0] for r in refined.execute("SELECT DISTINCT class_name FROM refined.race_wins")}
    assert classes == {"MotoGP", "Moto2", "500cc", "350cc", "250cc", "125cc"}


def test_race_wins_marca_categoria_principal(refined):
    principais = scalar(refined, "SELECT COUNT(*) FROM refined.race_wins WHERE is_premier_class = 1")
    assert principais == 4  # 2 MotoGP + 2 500cc


def test_race_wins_season_e_inteiro(refined):
    assert scalar(refined, "SELECT typeof(season) FROM refined.race_wins LIMIT 1") == "integer"


def test_join_race_wins_com_dimensoes(refined):
    """O JOIN principal do projeto: vitórias por piloto e fabricante."""
    linhas = refined.execute(
        """
        SELECT r.rider_name, k.constructor_name, COUNT(*)
        FROM refined.race_wins     AS w
        JOIN refined.riders        AS r USING (rider_id)
        JOIN refined.constructors  AS k USING (constructor_id)
        WHERE w.season = 2022 AND w.class_name = 'MotoGP'
        GROUP BY 1, 2
        """
    ).fetchall()
    assert linhas == [("Pecco Bagnaia", "Ducati", 2)]


# --- integridade referencial -----------------------------------------------

@pytest.mark.parametrize(
    ("tabela", "chave", "dimensao"),
    [
        ("race_wins", "rider_id", "riders"),
        ("race_wins", "constructor_id", "constructors"),
        ("constructor_championships", "constructor_id", "constructors"),
        ("rider_career_stats", "rider_id", "riders"),
    ],
)
def test_toda_chave_existe_na_dimensao(refined, tabela, chave, dimensao):
    orfaos = scalar(
        refined,
        f"""
        SELECT COUNT(*) FROM refined.{tabela} AS t
        LEFT JOIN refined.{dimensao} AS d USING ({chave})
        WHERE d.{chave} IS NULL
        """,
    )
    assert orfaos == 0


# --- demais tabelas --------------------------------------------------------

def test_constructor_championships(refined):
    linha = refined.execute(
        """
        SELECT c.season, c.class_name, c.is_premier_class, k.constructor_name
        FROM refined.constructor_championships AS c
        JOIN refined.constructors AS k USING (constructor_id)
        WHERE c.season = 2022 AND c.class_name = 'MotoGP'
        """
    ).fetchone()
    assert linha == (2022, "MotoGP", 1, "Ducati")


def test_career_stats_converte_vazio_em_nulo(refined):
    linha = refined.execute(
        """
        SELECT s.victories, s.fourth_places
        FROM refined.rider_career_stats AS s
        JOIN refined.riders AS r USING (rider_id)
        WHERE r.rider_name = 'Mick Doohan'
        """
    ).fetchone()
    assert linha == (54, None)


def test_podium_lockouts_le_coluna_com_acento_grave(refined):
    linhas = refined.execute(
        "SELECT season, class_name, nation_code FROM refined.podium_lockouts ORDER BY season"
    ).fetchall()
    assert linhas == [(2021, "MotoE", "IT"), (2022, "MotoGP", "ES")]


def test_refined_pode_rodar_duas_vezes(refined):
    build_refined(refined, SQL_DIR)
    assert scalar(refined, "SELECT COUNT(*) FROM refined.race_wins") == 8


def test_raw_continua_intacta(refined):
    """A refined lê a raw, mas não muda nada nela."""
    assert scalar(refined, "SELECT COUNT(*) FROM raw.grand_prix_race_winners") == 8
    assert scalar(
        refined, "SELECT COUNT(*) FROM raw.grand_prix_race_winners WHERE \"Class\" LIKE '%™'"
    ) == 3


def test_campos_em_branco_viram_membro_desconhecido(refined):
    linhas = refined.execute(
        """
        SELECT w.season, r.rider_name, k.constructor_name
        FROM refined.race_wins    AS w
        JOIN refined.riders       AS r USING (rider_id)
        JOIN refined.constructors AS k USING (constructor_id)
        WHERE 'Desconhecido' IN (r.rider_name, k.constructor_name)
        ORDER BY w.season
        """
    ).fetchall()
    assert linhas == [(1955, "Desconhecido", "MV Agusta"), (1999, "Valentino Rossi", "Desconhecido")]


def test_piloto_desconhecido_nao_tem_pais(refined):
    pais = scalar(refined, "SELECT country_code FROM refined.riders WHERE rider_name = 'Desconhecido'")
    assert pais is None


def test_career_stats_uma_linha_por_piloto(refined):
    total = scalar(refined, "SELECT COUNT(*) FROM refined.rider_career_stats")
    distintos = scalar(refined, "SELECT COUNT(DISTINCT rider_id) FROM refined.rider_career_stats")
    assert total == distintos == 5


def _carreira(conn, nome):
    return conn.execute(
        """
        SELECT s.victories, s.second_places, s.third_places
        FROM refined.rider_career_stats AS s
        JOIN refined.riders AS r USING (rider_id)
        WHERE r.rider_name = ?
        """,
        (nome,),
    ).fetchone()


def test_career_stats_linha_identica_conta_uma_vez(refined):
    assert _carreira(refined, "Loris Capirossi") == (29, 30, 40)


def test_career_stats_linhas_diferentes_sao_somadas(refined):
    assert _carreira(refined, "Nello Pagani") == (5, 2, 1)
