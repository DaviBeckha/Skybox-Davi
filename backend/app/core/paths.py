"""Caminhos locais do projeto (relativos à raiz do repositório)."""

from pathlib import Path

# paths.py -> app/core/paths.py ; raiz do repo = parents[3]
REPO_ROOT: Path = Path(__file__).resolve().parents[3]

DATA_DIR: Path = REPO_ROOT / "data"
RAW_DEMOS_DIR: Path = DATA_DIR / "raw_demos"
PARQUET_DIR: Path = DATA_DIR / "processed" / "parquet"
DUCKDB_DIR: Path = DATA_DIR / "processed" / "duckdb"
DUCKDB_PATH: Path = DUCKDB_DIR / "cs2_lab.duckdb"
MAPS_DIR: Path = DATA_DIR / "maps"
MAPS_RADARS_DIR: Path = MAPS_DIR / "radars"
MAPS_RADAR_INFO_DIR: Path = MAPS_DIR / "radar_info"


def ensure_dirs() -> None:
    """Garante que os diretórios de dados existem."""
    for d in (
        RAW_DEMOS_DIR,
        PARQUET_DIR,
        DUCKDB_DIR,
        MAPS_RADARS_DIR,
        MAPS_RADAR_INFO_DIR,
    ):
        d.mkdir(parents=True, exist_ok=True)
