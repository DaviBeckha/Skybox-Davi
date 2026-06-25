"""DuckDB local com views sobre os Parquet processados."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.parsers.schema import PARQUET_SCHEMAS


class DuckDBUnavailable(RuntimeError):
    """DuckDB não está instalado no ambiente Python atual."""


def _quote_sql(value: str) -> str:
    return value.replace("'", "''")


def refresh_views(parquet_dir: Path, duckdb_path: Path) -> Any:
    """Cria/atualiza views DuckDB sobre `match_id=*/<table>.parquet`.

    Retorna a conexão aberta para permitir validação imediata por quem chamou.
    O chamador é responsável por fechar a conexão.
    """
    try:
        import duckdb
    except ModuleNotFoundError as exc:  # pragma: no cover - depende do ambiente
        raise DuckDBUnavailable(
            "duckdb não está instalado; rode `uv add duckdb` ou `pip install duckdb`."
        ) from exc

    duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(duckdb_path))
    for table in PARQUET_SCHEMAS:
        pattern = (parquet_dir / "match_id=*" / f"{table}.parquet").as_posix()
        quoted_pattern = _quote_sql(pattern)
        connection.execute(
            f"""
            CREATE OR REPLACE VIEW {table} AS
            SELECT *
            FROM read_parquet(
                '{quoted_pattern}',
                hive_partitioning = 1,
                union_by_name = true
            )
            """
        )
    return connection
