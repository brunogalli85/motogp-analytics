"""Verificações de qualidade entre as camadas raw e refined.

Dois tipos de verificação:
- ERRO: quebra de reconciliação (linhas que se perderam entre raw e refined).
  O pipeline para, porque indicadores calculados sobre dados incompletos estariam errados.
- AVISO: dado suspeito na origem que foi tratado, mas merece registro
  (campos em branco, nomes duplicados). O pipeline segue.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# (tabela na raw, tabela na refined, contagem esperada na raw)
# Em geral a refined tem uma linha por linha da raw. A exceção é a carreira dos pilotos,
# consolidada em uma linha por piloto: ali o esperado é o número de pilotos distintos.
RECONCILIATIONS = [
    ("grand_prix_race_winners", "race_wins", "COUNT(*)"),
    ("constructure_world_championship", "constructor_championships", "COUNT(*)"),
    ("riders_finishing_positions", "rider_career_stats",
     "COUNT(DISTINCT TRIM(\"Rider\")) FILTER (WHERE TRIM(\"Rider\") <> '')"),
    ("same_nation_podium_lockouts", "podium_lockouts", "COUNT(*)"),
]


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str
    blocking: bool  # True = erro que interrompe o pipeline


def _count(conn: sqlite3.Connection, sql: str) -> int:
    return conn.execute(sql).fetchone()[0]


def check_reconciliation(conn: sqlite3.Connection) -> list[CheckResult]:
    """Toda linha da raw precisa chegar na refined."""
    results = []
    for raw_table, refined_table, expected_sql in RECONCILIATIONS:
        raw_rows = _count(conn, f"SELECT {expected_sql} FROM raw.{raw_table}")
        refined_rows = _count(conn, f"SELECT COUNT(*) FROM refined.{refined_table}")
        results.append(
            CheckResult(
                name=f"reconciliação {raw_table} -> {refined_table}",
                passed=raw_rows == refined_rows,
                detail=f"raw={raw_rows} refined={refined_rows}",
                blocking=True,
            )
        )
    return results


def check_unknown_members(conn: sqlite3.Connection) -> list[CheckResult]:
    """Vitórias com piloto ou fabricante em branco na origem."""
    results = []
    for dimension, key, name_col in [
        ("riders", "rider_id", "rider_name"),
        ("constructors", "constructor_id", "constructor_name"),
    ]:
        total = _count(
            conn,
            f"""
            SELECT COUNT(*) FROM refined.race_wins AS w
            JOIN refined.{dimension} AS d USING ({key})
            WHERE d.{name_col} = 'Desconhecido'
            """,
        )
        results.append(
            CheckResult(
                name=f"vitórias com {dimension} em branco na origem",
                passed=total == 0,
                detail=f"{total} vitória(s) atribuída(s) a 'Desconhecido'",
                blocking=False,
            )
        )
    return results


def check_duplicate_career_names(conn: sqlite3.Connection) -> list[CheckResult]:
    """Pilotos que aparecem mais de uma vez em riders_finishing_positions."""
    rows = conn.execute(
        """
        SELECT TRIM("Rider") AS rider, COUNT(*) AS vezes
        FROM raw.riders_finishing_positions
        GROUP BY TRIM("Rider")
        HAVING COUNT(*) > 1
        ORDER BY rider
        """
    ).fetchall()
    names = ", ".join(f"{rider} ({times}x)" for rider, times in rows)
    return [
        CheckResult(
            name="nomes repetidos em riders_finishing_positions (consolidados na refined)",
            passed=not rows,
            detail=names or "nenhum",
            blocking=False,
        )
    ]


def run_checks(conn: sqlite3.Connection) -> list[CheckResult]:
    """Executa todas as verificações e registra o resultado no log."""
    results = (
        check_reconciliation(conn)
        + check_unknown_members(conn)
        + check_duplicate_career_names(conn)
    )
    for result in results:
        if result.passed:
            logger.info("OK     | %s | %s", result.name, result.detail)
        elif result.blocking:
            logger.error("ERRO   | %s | %s", result.name, result.detail)
        else:
            logger.warning("AVISO  | %s | %s", result.name, result.detail)
    return results


def has_blocking_failure(results: list[CheckResult]) -> bool:
    return any(r.blocking and not r.passed for r in results)
