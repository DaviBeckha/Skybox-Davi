"""Posições de morte e cluster simples de top spot."""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.analytics.map_projection import RadarMetadata, world_to_radar
from app.analytics.reader import read_table


def build_death_positions(
    match_id: str, map_name: str, steam_id: str, metadata: RadarMetadata
) -> dict[str, Any]:
    deaths = []
    buckets: Counter[tuple[int, int]] = Counter()
    bucket_points: dict[tuple[int, int], tuple[float, float]] = {}
    for kill in read_table(match_id, "kills"):
        if kill["victim_steam_id"] != steam_id:
            continue
        x = float(kill["victim_x"])
        y = float(kill["victim_y"])
        radar = world_to_radar(x, y, metadata)
        deaths.append(
            {
                "round_number": kill["round_number"],
                "x": x,
                "y": y,
                **radar,
                "attacker_steam_id": kill["attacker_steam_id"],
                "weapon": kill["weapon"],
            }
        )
        bucket = (round(x / 128), round(y / 128))
        buckets[bucket] += 1
        bucket_points[bucket] = (x, y)

    top_spot = None
    if buckets:
        bucket, count = buckets.most_common(1)[0]
        x, y = bucket_points[bucket]
        top_spot = {
            "x": x,
            "y": y,
            **world_to_radar(x, y, metadata),
            "count": count,
            "cluster_radius": 128,
        }
    return {
        "match_id": match_id,
        "steam_id": steam_id,
        "map": map_name,
        "deaths": deaths,
        "top_spot": top_spot,
    }
