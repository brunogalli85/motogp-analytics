"""Mostra o perfil da camada raw: tabelas, colunas, quantidade de linhas e amostra.

Uso: python -m motogp.profile
Serve para conhecer os dados antes de escrever a camada refined.
"""

from __future__ import annotations

from motogp.config import get_settings
from motogp.db import connect, list_tables
from motogp.raw import quote_identifier


def main() -> None:
    settings = get_settings()
    conn = connect(settings.warehouse_dir)

    tables = list_tables(conn, "raw")
    if not tables:
        print("Camada raw vazia. Rode o pipeline primeiro.")
        return

    for table in tables:
        target = f"raw.{quote_identifier(table)}"
        total = conn.execute(f"SELECT COUNT(*) FROM {target}").fetchone()[0]
        cursor = conn.execute(f"SELECT * FROM {target} LIMIT 3")
        columns = [desc[0] for desc in cursor.description]

        print(f"\n=== raw.{table} ({total} linhas) ===")
        print("Colunas:", ", ".join(columns))
        for row in cursor.fetchall():
            print("  ", row)

    conn.close()


if __name__ == "__main__":
    main()
