"""Fixtures compartilhadas. Nenhum teste abre o banco real do projeto."""

import pytest

from motogp.db import connect


@pytest.fixture
def warehouse():
    """Warehouse com as três camadas, todo em memória e descartado ao fim do teste."""
    conn = connect(None)
    yield conn
    conn.close()


@pytest.fixture
def write_csv(tmp_path):
    """Cria um CSV inventado numa pasta temporária e devolve o caminho."""

    def _write(name: str, content: str, encoding: str = "utf-8"):
        path = tmp_path / name
        path.write_bytes(content.encode(encoding))
        return path

    return _write
