"""Configurações do projeto, lidas de variáveis de ambiente (arquivo .env)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DATASET = "alrizacelk/moto-gp-world-championship19492022"


@dataclass(frozen=True)
class Settings:
    """Parâmetros do pipeline. Imutável para evitar alterações acidentais."""

    kaggle_dataset: str
    landing_dir: Path    # CSVs exatamente como vieram do Kaggle
    warehouse_dir: Path  # bancos SQLite: raw.db, refined.db, marts.db
    sql_dir: Path        # consultas SQL das camadas refined e marts
    log_level: str


def get_settings() -> Settings:
    """Carrega o .env (se existir) e monta as configurações com valores padrão."""
    load_dotenv(PROJECT_ROOT / ".env")

    return Settings(
        kaggle_dataset=os.getenv("KAGGLE_DATASET", DEFAULT_DATASET),
        landing_dir=Path(os.getenv("LANDING_DIR", PROJECT_ROOT / "data" / "landing")),
        warehouse_dir=Path(os.getenv("WAREHOUSE_DIR", PROJECT_ROOT / "data" / "warehouse")),
        sql_dir=PROJECT_ROOT / "sql",
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
