"""Mostra o perfil de uma camada: tabelas, colunas, quantidade de linhas e amostra.

Uso:
    python -m motogp.profile            # camada raw (padrão)
    python -m motogp.profile refined
    python -m motogp.profile marts
"""

from __future__ import annotations

import argparse

from motogp.config import get_settings
from motogp.db import LAYERS, connect, list_tables
from motogp.raw import quote_identifier


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Perfil de uma camada do warehouse")
    parser.add_argument("layer", nargs="?", default="raw", choices=LAYERS)
    layer = parser.parse_args(argv).layer

    settings = get_settings()
    conn = connect(settings.warehouse_dir)

    tables = list_tables(conn, layer)
    if not tables:
        print(f"Camada {layer} vazia. Rode o pipeline primeiro.")
        conn.close()
        return

    for table in tables:
        target = f"{layer}.{quote_identifier(table)}"
        total = conn.execute(f"SELECT COUNT(*) FROM {target}").fetchone()[0]
        cursor = conn.execute(f"SELECT * FROM {target} LIMIT 3")
        columns = [desc[0] for desc in cursor.description]

        print(f"\n=== {layer}.{table} ({total} linhas) ===")
        print("Colunas:", ", ".join(columns))
        for row in cursor.fetchall():
            print("  ", row)

    conn.close()


if __name__ == "__main__":
    main()
