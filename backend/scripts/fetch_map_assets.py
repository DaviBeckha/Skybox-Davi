"""Popula data/maps/ com radares e metadados oficiais via awpy.

Os overviews vêm dos arquivos do CS2 (distribuídos pelo awpy) — fonte legítima
para uso local de análise. Os binários NÃO são versionados; rode este script
para baixá-los e popular `data/maps/radars/` e `data/maps/radar_info/`.

Uso:
    uv run python -m scripts.fetch_map_assets          # baixa (se preciso) e copia
"""

from __future__ import annotations

import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path

from awpy.data import MAPS_DIR

from app.core import paths

# Mapas que nos interessam (ignora variações *_lower de mapas multi-nível por ora).
_PREFIXES = ("de_", "cs_", "ar_")


def _png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        return (1024, 1024)
    width, height = struct.unpack(">II", header[16:24])
    return (width, height)


def main() -> int:
    maps_dir = Path(MAPS_DIR)
    if not maps_dir.exists() or not any(maps_dir.glob("*.png")):
        print("Baixando mapas via awpy (awpy get maps)...")
        subprocess.run([sys.executable, "-m", "awpy", "get", "maps"], check=True)

    map_data_path = maps_dir / "map-data.json"
    map_data: dict[str, dict] = {}
    if map_data_path.exists():
        map_data = json.loads(map_data_path.read_text(encoding="utf-8"))

    paths.MAPS_RADARS_DIR.mkdir(parents=True, exist_ok=True)
    paths.MAPS_RADAR_INFO_DIR.mkdir(parents=True, exist_ok=True)

    copied = 0
    for png in sorted(maps_dir.glob("*.png")):
        name = png.stem
        if name.endswith("_lower") or not name.startswith(_PREFIXES):
            continue
        shutil.copyfile(png, paths.MAPS_RADARS_DIR / f"{name}.png")
        width, height = _png_size(png)
        info = map_data.get(name, {})
        metadata = {
            "map": name,
            "pos_x": float(info.get("pos_x", -4096)),
            "pos_y": float(info.get("pos_y", 4096)),
            "scale": float(info.get("scale", 8.0)),
            "image_width": width,
            "image_height": height,
            "levels": None,
        }
        (paths.MAPS_RADAR_INFO_DIR / f"{name}.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        copied += 1
        print(
            f"  {name}: {width}x{height} "
            f"(pos {metadata['pos_x']},{metadata['pos_y']} scale {metadata['scale']})"
        )

    print(f"OK: {copied} mapas copiados para {paths.MAPS_RADARS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
