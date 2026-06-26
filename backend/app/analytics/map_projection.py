"""Conversão de coordenadas do mundo da demo para coordenadas de radar."""

from __future__ import annotations

from typing import TypedDict


class RadarMetadata(TypedDict):
    map: str
    pos_x: float
    pos_y: float
    scale: float
    image_width: int
    image_height: int
    levels: object | None


def world_to_radar(
    x: float | None, y: float | None, metadata: RadarMetadata
) -> dict[str, float | None]:
    """Aplica a fórmula normativa do contrato de dados."""
    if x is None or y is None:
        return {"radar_x": None, "radar_y": None}
    return {
        "radar_x": (float(x) - float(metadata["pos_x"])) / float(metadata["scale"]),
        "radar_y": (float(metadata["pos_y"]) - float(y)) / float(metadata["scale"]),
    }
