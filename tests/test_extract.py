import sys
import types

import pytest

from motogp.extract import ExtractError, copy_csvs, extract


def _fake_kagglehub(monkeypatch, download):
    """Substitui o kagglehub por um módulo falso: os testes não acessam a internet."""
    module = types.SimpleNamespace(dataset_download=download)
    monkeypatch.setitem(sys.modules, "kagglehub", module)


def test_copy_csvs_inclui_subpastas_e_ignora_outros_arquivos(tmp_path):
    source = tmp_path / "cache"
    (source / "sub").mkdir(parents=True)
    (source / "a.csv").write_text("x\n1\n")
    (source / "sub" / "b.csv").write_text("y\n2\n")
    (source / "leia-me.txt").write_text("ignorar")

    copied = copy_csvs(source, tmp_path / "raw")

    assert sorted(p.name for p in copied) == ["a.csv", "b.csv"]


def test_copy_csvs_sem_csv_gera_erro(tmp_path):
    with pytest.raises(ExtractError):
        copy_csvs(tmp_path, tmp_path / "raw")


def test_extract_usa_kagglehub(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "races.csv").write_text("year\n2022\n")
    _fake_kagglehub(monkeypatch, lambda handle: str(cache))

    copied = extract("dono/dataset", tmp_path / "raw")

    assert [p.name for p in copied] == ["races.csv"]


def test_extract_converte_falha_de_download_em_extract_error(tmp_path, monkeypatch):
    def falha(handle):
        raise ConnectionError("sem internet")

    _fake_kagglehub(monkeypatch, falha)

    with pytest.raises(ExtractError, match="sem internet"):
        extract("dono/dataset", tmp_path / "raw")
