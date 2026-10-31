"""Etapa de extração: baixa o dataset do Kaggle via API e copia os CSVs para data/raw."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class ExtractError(RuntimeError):
    """Falha ao obter os dados do Kaggle."""


def download_dataset(handle: str) -> Path:
    """Baixa o dataset com kagglehub e devolve a pasta (cache) onde ele foi salvo.

    A autenticação usa o token do Kaggle guardado fora do código
    (variáveis de ambiente ou ~/.kaggle/kaggle.json).
    """
    try:
        import kagglehub
    except ImportError as exc:
        raise ExtractError("Pacote 'kagglehub' não instalado. Rode: uv sync") from exc

    logger.info("Baixando dataset '%s' do Kaggle...", handle)
    try:
        path = Path(kagglehub.dataset_download(handle))
    except Exception as exc:  # erros de rede, autenticação ou dataset inexistente
        raise ExtractError(f"Falha ao baixar '{handle}': {exc}") from exc

    logger.info("Download concluído em %s", path)
    return path


def copy_csvs(source_dir: Path, raw_dir: Path) -> list[Path]:
    """Copia todos os CSVs (inclusive em subpastas) para raw_dir e devolve a lista copiada."""
    csv_files = sorted(source_dir.rglob("*.csv"))
    if not csv_files:
        raise ExtractError(f"Nenhum arquivo CSV encontrado em {source_dir}")

    raw_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for csv_file in csv_files:
        destination = raw_dir / csv_file.name
        shutil.copy2(csv_file, destination)
        copied.append(destination)
        logger.info("Copiado: %s", csv_file.name)

    return copied


def extract(handle: str, raw_dir: Path) -> list[Path]:
    """Executa a extração completa: download + cópia para a pasta de dados brutos."""
    source_dir = download_dataset(handle)
    return copy_csvs(source_dir, raw_dir)
