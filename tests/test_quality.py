"""Testes das verificações de qualidade, com tabelas mínimas inventadas em memória."""

import pytest

from motogp.quality import (
    CheckResult,
    check_duplicate_career_names,
    check_reconciliation,
    check_unknown_members,
    has_blocking_failure,
)


@pytest.fixture
def camadas(warehouse):
    warehouse.executescript(
        """
        CREATE TABLE raw.grand_prix_race_winners (x TEXT);
        CREATE TABLE raw.constructure_world_championship (x TEXT);
        CREATE TABLE raw.riders_finishing_positions ("Rider" TEXT);
        CREATE TABLE raw.same_nation_podium_lockouts (x TEXT);
        INSERT INTO raw.grand_prix_race_winners VALUES ('a'), ('b'), ('c');
        INSERT INTO raw.riders_finishing_positions VALUES ('Rossi'), (' Rossi'), ('Marquez');

        CREATE TABLE refined.riders (rider_id INTEGER, rider_name TEXT);
        CREATE TABLE refined.constructors (constructor_id INTEGER, constructor_name TEXT);
        CREATE TABLE refined.race_wins (rider_id INTEGER, constructor_id INTEGER);
        CREATE TABLE refined.constructor_championships (x TEXT);
        CREATE TABLE refined.rider_career_stats (x TEXT);
        CREATE TABLE refined.podium_lockouts (x TEXT);
        INSERT INTO refined.riders VALUES (1, 'Rossi'), (2, 'Desconhecido');
        INSERT INTO refined.constructors VALUES (1, 'Honda');
        INSERT INTO refined.race_wins VALUES (1, 1), (2, 1);
        INSERT INTO refined.rider_career_stats VALUES ('r'), ('m');
        """
    )
    return warehouse


def _por_nome(resultados):
    return {r.name.split(" -> ")[0].removeprefix("reconciliação "): r for r in resultados}


def test_reconciliacao_detecta_linhas_perdidas(camadas):
    r = _por_nome(check_reconciliation(camadas))
    assert not r["grand_prix_race_winners"].passed           # 3 na raw, 2 na refined
    assert r["grand_prix_race_winners"].detail == "raw=3 refined=2"
    assert r["riders_finishing_positions"].passed            # 2 pilotos distintos e 2
    assert r["constructure_world_championship"].passed       # 0 e 0


def test_membro_desconhecido_gera_aviso(camadas):
    pilotos, fabricantes = check_unknown_members(camadas)
    assert not pilotos.passed and not pilotos.blocking
    assert pilotos.detail.startswith("1 vitória")
    assert fabricantes.passed


def test_nomes_repetidos_considera_espacos(camadas):
    (resultado,) = check_duplicate_career_names(camadas)
    assert not resultado.passed
    assert resultado.detail == "Rossi (2x)"


def test_so_erro_bloqueante_interrompe():
    aviso = CheckResult("a", passed=False, detail="", blocking=False)
    erro = CheckResult("b", passed=False, detail="", blocking=True)
    ok = CheckResult("c", passed=True, detail="", blocking=True)
    assert not has_blocking_failure([aviso, ok])
    assert has_blocking_failure([aviso, erro])
