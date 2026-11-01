"""Testes da camada marts.

Uma raw inventada e pequena, com resultados que dá para conferir de cabeça,
passa pelo SQL real de refined e marts do projeto. Tudo em memória.

Vitórias inventadas:
    1998 500cc   Mick Doohan (AU)  Honda   x2
    1998 500cc   Max Biaggi (IT)   Yamaha  x1
    1998 500cc   Max Biaggi (IT)   (em branco -> Desconhecido) x1
    2022 MotoGP  Pecco Bagnaia (IT) Ducati x2
    2022 MotoGP  Fabio Quartararo (FR) Yamaha x1
    2022 Moto3   Jaume Masia (ES)  KTM     x1   (não é categoria principal)
"""

from pathlib import Path

import pytest

from motogp.transform import build_marts, build_refined

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"

RAW = {
    "grand_prix_race_winners": (
        ["Circuit", "Class", "Constructor", "Country", "Rider", "Season"],
        [
            ("Assen", "500cc", "Honda", "AU", "Mick Doohan", "1998"),
            ("Mugello", "500cc", "Honda", "AU", "Mick Doohan", "1998"),
            ("Jerez", "500cc", "Yamaha", "IT", "Max Biaggi", "1998"),
            ("Brno", "500cc", "", "IT", "Max Biaggi", "1998"),
            ("Mugello", "MotoGP™", "Ducati", "IT", "Pecco Bagnaia", "2022"),
            ("Assen", "MotoGP™", "Ducati", "IT", "Pecco Bagnaia", "2022"),
            ("Jerez", "MotoGP™", "Yamaha", "FR", "Fabio Quartararo", "2022"),
            ("Jerez", "Moto3™", "KTM", "ES", "Jaume Masia", "2022"),
        ],
    ),
    "constructure_world_championship": (
        ["Season", "Constructor", "Class"],
        [("1998", "Honda", "500cc"), ("2022", "Ducati", "MotoGP™"), ("2022", "KTM", "Moto3™")],
    ),
    "same_nation_podium_lockouts": (
        ["Season", "Track", "Riders` Nation", "Class"],
        [
            ("1998", "Mugello", "IT", "500cc"),
            ("2022", "Jerez", "ES", "MotoGP™"),
            ("2021", "Valencia", "ES", "Moto3™"),
        ],
    ),
    "riders_finishing_positions": (
        ["Rider", "Victories", "NumberofSecond", "NumberofThird",
         "Numberof4th", "Numberof5th", "Numberof6th", "Country"],
        [],
    ),
    "grand_prix_events_held": (["Times", "Track", "Country"], [("280", "Assen", "NL")]),
}


@pytest.fixture
def marts(warehouse):
    for table, (columns, rows) in RAW.items():
        cols = ", ".join(f'"{c}" TEXT' for c in columns)
        warehouse.execute(f"CREATE TABLE raw.{table} ({cols})")
        marks = ", ".join("?" for _ in columns)
        warehouse.executemany(f"INSERT INTO raw.{table} VALUES ({marks})", rows)

    build_refined(warehouse, SQL_DIR)
    build_marts(warehouse, SQL_DIR)
    return warehouse


def rows(conn, sql):
    return conn.execute(sql).fetchall()


def test_constructor_wins_by_decade(marts):
    assert rows(
        marts,
        """
        SELECT decade, constructor_name, wins, decade_total_wins, share_pct, rank_in_decade
        FROM marts.constructor_wins_by_decade ORDER BY decade, rank_in_decade
        """,
    ) == [
        # 1990: 4 vitórias no total (inclusive a de fabricante desconhecido)
        (1990, "Honda", 2, 4, 50.0, 1),
        (1990, "Yamaha", 1, 4, 25.0, 2),
        # 2020: só a categoria principal entra; a vitória da Moto3 fica fora
        (2020, "Ducati", 2, 3, 66.7, 1),
        (2020, "Yamaha", 1, 3, 33.3, 2),
    ]


def test_constructor_wins_nao_mostra_desconhecido(marts):
    assert not rows(
        marts, "SELECT 1 FROM marts.constructor_wins_by_decade WHERE constructor_name = 'Desconhecido'"
    )


def test_champion_dominance_so_categoria_principal(marts):
    assert rows(marts, "SELECT * FROM marts.champion_dominance ORDER BY season") == [
        (1998, "Honda", 2, 4, 50.0),
        (2022, "Ducati", 2, 3, 66.7),
    ]


def test_top_riders_premier(marts):
    assert rows(marts, "SELECT * FROM marts.top_riders_premier") == [
        # empate em 2 vitórias divide o 1º lugar
        (1, "Max Biaggi", "IT", 2, 1, 1998, 1998),
        (1, "Mick Doohan", "AU", 2, 1, 1998, 1998),
        (1, "Pecco Bagnaia", "IT", 2, 1, 2022, 2022),
        (2, "Fabio Quartararo", "FR", 1, 1, 2022, 2022),
    ]


def test_top_riders_ignora_categorias_menores(marts):
    assert not rows(marts, "SELECT 1 FROM marts.top_riders_premier WHERE rider_name = 'Jaume Masia'")


def test_wins_by_country_decade(marts):
    assert rows(
        marts,
        """
        SELECT decade, country_code, wins, premier_class_wins, share_pct, rank_in_decade
        FROM marts.wins_by_country_decade ORDER BY decade, rank_in_decade, country_code
        """,
    ) == [
        (1990, "AU", 2, 2, 50.0, 1),
        (1990, "IT", 2, 2, 50.0, 1),
        (2020, "IT", 2, 2, 50.0, 1),
        (2020, "ES", 1, 0, 25.0, 2),
        (2020, "FR", 1, 1, 25.0, 2),
    ]


def test_podium_lockouts_by_nation(marts):
    assert rows(marts, "SELECT * FROM marts.podium_lockouts_by_nation ORDER BY decade") == [
        (1990, "IT", 1, 1),
        (2020, "ES", 2, 1),
    ]


def test_kpi_summary(marts):
    assert rows(marts, "SELECT * FROM marts.kpi_summary") == [
        # temporadas, vitórias, vitórias na principal, pilotos, fabricantes (sem Desconhecido), países
        (1998, 2022, 8, 7, 5, 4, 4),
    ]


def test_marts_podem_rodar_duas_vezes(marts):
    build_marts(marts, SQL_DIR)
    assert rows(marts, "SELECT COUNT(*) FROM marts.champion_dominance") == [(2,)]
