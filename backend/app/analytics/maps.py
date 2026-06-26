"""Assets locais de mapa: metadata de overview e imagens de radar.

A imagem de radar real (overview do CS2) é um asset externo. Quando um arquivo
`data/maps/radars/<map>.png` real existe, ele é servido como está. Caso
contrário, geramos um **placeholder do tamanho correto** (a partir do
`image_width`/`image_height` do metadata) para que o frontend tenha um canvas
nas dimensões certas — basta dropar o overview real no diretório para substituí-lo.
"""

from __future__ import annotations

import json
import logging
import re
import struct
import zlib
from pathlib import Path
from typing import Any

from app.analytics.map_projection import RadarMetadata
from app.core import paths

logger = logging.getLogger("cs2-lab.maps")

# Constantes de overview (pos_x, pos_y, scale) dos mapas do competitivo.
# Fonte: valores públicos de overview do CS2 (compatíveis com awpy/SimpleRadar).
# Podem ser substituídas por arquivos em data/maps/radar_info/<map>.json.
_MAP_OVERVIEWS: dict[str, tuple[float, float, float]] = {
    "de_ancient": (-2953, 2164, 5.0),
    "de_anubis": (-2796, 3328, 5.22),
    "de_dust2": (-2476, 3239, 4.4),
    "de_inferno": (-2087, 3870, 4.9),
    "de_mirage": (-3230, 1713, 5.0),
    "de_nuke": (-3453, 2887, 7.0),
    "de_overpass": (-4831, 1781, 5.2),
    "de_train": (-2308, 2078, 4.082),
    "de_vertigo": (-3168, 1762, 4.0),
}


def _overview(map_name: str, pos_x: float, pos_y: float, scale: float) -> RadarMetadata:
    return {
        "map": map_name,
        "pos_x": pos_x,
        "pos_y": pos_y,
        "scale": scale,
        "image_width": 1024,
        "image_height": 1024,
        "levels": None,
    }


DEFAULT_MAP_METADATA: dict[str, RadarMetadata] = {
    name: _overview(name, x, y, scale) for name, (x, y, scale) in _MAP_OVERVIEWS.items()
}

# Projeção genérica para mapas desconhecidos: mantém coordenadas de mundo
# (~±4096) dentro do canvas 0..1024 sem quebrar replay/heatmap.
_GENERIC_OVERVIEW: tuple[float, float, float] = (-4096.0, 4096.0, 8.0)

_SAFE_MAP_NAME = re.compile(r"^[a-z0-9_]+$")

# Cache de placeholders renderizados por (width, height).
_placeholder_cache: dict[tuple[int, int], bytes] = {}


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def _render_placeholder_png(width: int, height: int) -> bytes:
    """Gera um PNG RGB do tamanho pedido (fundo escuro + grid), só com stdlib."""
    cached = _placeholder_cache.get((width, height))
    if cached is not None:
        return cached

    background = bytes((24, 28, 34))
    grid = bytes((45, 52, 64))
    step = 128
    normal_line = bytearray([0])  # filtro 0
    for x in range(width):
        normal_line += grid if x % step == 0 else background
    grid_line = bytes([0]) + grid * width

    raw = bytearray()
    for y in range(height):
        raw += grid_line if y % step == 0 else normal_line

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _png_chunk(b"IEND", b"")
    )
    _placeholder_cache[(width, height)] = png
    return png


def _placeholder_for(map_name: str) -> bytes:
    try:
        metadata = load_metadata(map_name)
        width = int(metadata.get("image_width") or 1024)
        height = int(metadata.get("image_height") or 1024)
    except (FileNotFoundError, KeyError, TypeError, ValueError):
        width = height = 1024
    return _render_placeholder_png(width, height)


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
            width = int(metadata.get("image_width") or 1024)
            height = int(metadata.get("image_height") or 1024)
            radar_path.write_bytes(_render_placeholder_png(width, height))


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
    if not _SAFE_MAP_NAME.match(map_name or ""):
        raise FileNotFoundError(map_name)
    metadata_path = paths.MAPS_RADAR_INFO_DIR / f"{map_name}.json"
    if metadata_path.exists():
        raw: dict[str, Any] = json.loads(metadata_path.read_text(encoding="utf-8"))
    elif map_name in DEFAULT_MAP_METADATA:
        raw = dict(DEFAULT_MAP_METADATA[map_name])
    else:
        # Mapa sem overview conhecido: usa projeção genérica em vez de quebrar
        # replay/heatmap. Coloque data/maps/radar_info/<map>.json para o real.
        logger.warning("Overview do mapa '%s' desconhecido; usando projeção genérica.", map_name)
        gx, gy, gscale = _GENERIC_OVERVIEW
        raw = _overview(map_name, gx, gy, gscale)
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
    if not _SAFE_MAP_NAME.match(map_name or ""):
        raise FileNotFoundError(map_name)
    candidate = paths.MAPS_RADARS_DIR / f"{map_name}.png"
    if not candidate.exists():
        # Sempre serve um placeholder do tamanho certo (substituível pelo radar real).
        candidate.write_bytes(_placeholder_for(map_name))
    return candidate
