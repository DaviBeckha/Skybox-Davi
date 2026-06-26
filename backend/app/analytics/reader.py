"""Leitura das tabelas Parquet particionadas por partida."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl

from app.core import paths
from app.parsers.schema import PARQUET_SCHEMAS, to_frame


def match_dir(match_id: str) -> Path:
    return paths.PARQUET_DIR / f"match_id={match_id}"


def read_table(match_id: str, table: str) -> list[dict[str, Any]]:
    parquet_path = match_dir(match_id) / f"{table}.parquet"
    if not parquet_path.exists():
        return to_frame(table, []).to_dicts()
    frame = pl.read_parquet(parquet_path)
    # Garante ordem/colunas do contrato mesmo se o arquivo tiver metadata extra.
    return frame.select(list(PARQUET_SCHEMAS[table])).to_dicts()


def read_tables(match_id: str, *table_names: str) -> dict[str, list[dict[str, Any]]]:
    return {table: read_table(match_id, table) for table in table_names}
