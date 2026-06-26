"""Assets locais de mapa: metadata de overview e imagens de radar."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.analytics.map_projection import RadarMetadata
from app.core import paths

DEFAULT_MAP_METADATA: dict[str, RadarMetadata] = {
    # Metadata usada como fallback local do MVP. Pode ser substituída por arquivos
    # extraídos da instalação do CS2 em data/maps/radar_info/<map>.json.
    "de_mirage": {
        "map": "de_mirage",
        "pos_x": -3230,
        "pos_y": 1713,
        "scale": 5.0,
        "image_width": 1024,
        "image_height": 1024,
        "levels": None,
    }
}

_PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360f8ffff3f0005fe02fea73581e40000000049454e44ae426082"
)


def ensure_default_assets() -> None:
    paths.MAPS_RADAR_INFO_DIR.mkdir(parents=True, exist_ok=True)
    paths.MAPS_RADARS_DIR.mkdir(parents=True, exist_ok=True)
    for map_name, metadata in DEFAULT_MAP_METADATA.items():
        metadata_path = paths.MAPS_RADAR_INFO_DIR / f"{map_name}.json"
        if not metadata_path.exists():
            metadata_path.write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        radar_path = paths.MAPS_RADARS_DIR / f"{map_name}.png"
        if not radar_path.exists():
            radar_path.write_bytes(_PNG_1X1)


def list_maps() -> list[RadarMetadata]:
    ensure_default_assets()
    result: list[RadarMetadata] = []
    seen: set[str] = set()
    for metadata_path in sorted(paths.MAPS_RADAR_INFO_DIR.glob("*.json")):
        metadata = load_metadata(metadata_path.stem)
        result.append(metadata)
        seen.add(metadata["map"])
    for map_name, metadata in DEFAULT_MAP_METADATA.items():
        if map_name not in seen:
            result.append(metadata)
    return result


def load_metadata(map_name: str) -> RadarMetadata:
    ensure_default_assets()
    metadata_path = paths.MAPS_RADAR_INFO_DIR / f"{map_name}.json"
    if metadata_path.exists():
        raw: dict[str, Any] = json.loads(metadata_path.read_text(encoding="utf-8"))
    elif map_name in DEFAULT_MAP_METADATA:
        raw = dict(DEFAULT_MAP_METADATA[map_name])
    else:
        raise FileNotFoundError(map_name)
    return {
        "map": str(raw.get("map", map_name)),
        "pos_x": float(raw["pos_x"]),
        "pos_y": float(raw["pos_y"]),
        "scale": float(raw["scale"]),
        "image_width": int(raw.get("image_width", 1024)),
        "image_height": int(raw.get("image_height", 1024)),
        "levels": raw.get("levels"),
    }


def radar_path(map_name: str) -> Path:
    ensure_default_assets()
    candidate = paths.MAPS_RADARS_DIR / f"{map_name}.png"
    if not candidate.exists():
        if map_name not in DEFAULT_MAP_METADATA:
            raise FileNotFoundError(map_name)
        candidate.write_bytes(_PNG_1X1)
    return candidate
