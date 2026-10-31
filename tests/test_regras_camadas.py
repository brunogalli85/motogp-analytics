"""Regras de separação entre camadas, verificadas lendo os arquivos .sql do projeto.

Estes testes não abrem banco nenhum: só leem o texto das consultas.
"""

import re
from pathlib import Path

import pytest

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"

ESCRITA_NA_RAW = re.compile(
    r"\b(INSERT\s+INTO|UPDATE|DELETE\s+FROM|CREATE\s+TABLE|DROP\s+TABLE(\s+IF\s+EXISTS)?|ALTER\s+TABLE)\s+raw\.",
    re.IGNORECASE,
)
LEITURA_DA_RAW = re.compile(r"\braw\.", re.IGNORECASE)
LEITURA_DOS_MARTS = re.compile(r"\b(FROM|JOIN)\s+marts\.", re.IGNORECASE)


def _sql_files(layer: str) -> list[Path]:
    return sorted((SQL_DIR / layer).glob("*.sql"))


def _todos() -> list[Path]:
    return _sql_files("refined") + _sql_files("marts")


@pytest.mark.parametrize("sql_file", _todos(), ids=lambda p: p.name)
def test_nenhuma_consulta_altera_a_raw(sql_file):
    assert not ESCRITA_NA_RAW.search(sql_file.read_text(encoding="utf-8"))


@pytest.mark.parametrize("sql_file", _sql_files("marts"), ids=lambda p: p.name)
def test_marts_nao_leem_direto_da_raw(sql_file):
    assert not LEITURA_DA_RAW.search(sql_file.read_text(encoding="utf-8"))


@pytest.mark.parametrize("sql_file", _sql_files("refined"), ids=lambda p: p.name)
def test_refined_nao_depende_dos_marts(sql_file):
    assert not LEITURA_DOS_MARTS.search(sql_file.read_text(encoding="utf-8"))


def test_regex_detecta_violacoes():
    """Garante que as regras acima de fato pegam um SQL errado."""
    assert ESCRITA_NA_RAW.search("UPDATE raw.results SET x = 1")
    assert ESCRITA_NA_RAW.search("drop table if exists raw.results")
    assert LEITURA_DA_RAW.search("SELECT * FROM raw.results")
    assert LEITURA_DOS_MARTS.search("SELECT * FROM marts.pontos")
    assert not ESCRITA_NA_RAW.search("CREATE TABLE refined.x AS SELECT * FROM raw.results")
