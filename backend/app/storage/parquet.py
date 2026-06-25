"""Escrita dos Parquet analíticos no schema canônico."""

from __future__ import annotations

import shutil
from pathlib import Path

from app.parsers.schema import PARQUET_SCHEMAS, to_frame


def write_parquet_tables(match_id: str, tables: dict[str, list[dict]], parquet_dir: Path) -> Path:
    """Grava todas as tabelas em `match_id=<uuid>/`.

    A escrita é feita em diretório temporário e então promovida, evitando sobras
    parciais quando uma falha ocorre no meio do processamento.
    """
    parquet_dir.mkdir(parents=True, exist_ok=True)
    final_dir = parquet_dir / f"match_id={match_id}"
    tmp_dir = parquet_dir / f".match_id={match_id}.tmp"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True)

    for table in PARQUET_SCHEMAS:
        rows = tables.get(table, [])
        to_frame(table, rows).write_parquet(tmp_dir / f"{table}.parquet")

    if final_dir.exists():
        shutil.rmtree(final_dir)
    tmp_dir.rename(final_dir)
    return final_dir
