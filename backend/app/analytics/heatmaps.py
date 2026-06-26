"""Pontos de heatmap para kills, deaths, pathing e utility."""

from __future__ import annotations

from typing import Any

from app.analytics.map_projection import RadarMetadata, world_to_radar
from app.analytics.reader import read_tables


def build_heatmap(
    match_id: str,
    map_name: str,
    heatmap_type: str,
    metadata: RadarMetadata,
    *,
    player: str | None = None,
    team: str | None = None,
    side: str | None = None,
    round_range: str | None = None,
    weapon: str | None = None,
    grenade_type: str | None = None,
) -> dict[str, Any]:
    tables = read_tables(match_id, "kills", "ticks", "grenades", "players")
    team_by_player = {row["steam_id"]: row.get("team") for row in tables["players"]}
    points: list[dict[str, Any]] = []

    if heatmap_type == "kills":
        for row in tables["kills"]:
            if _skip_player(row["attacker_steam_id"], player, team, team_by_player):
                continue
            if side and row["attacker_side"] != side:
                continue
            if weapon and row["weapon"] != weapon:
                continue
            points.append(_point(row["attacker_x"], row["attacker_y"], metadata))
    elif heatmap_type == "deaths":
        for row in tables["kills"]:
            if _skip_player(row["victim_steam_id"], player, team, team_by_player):
                continue
            if side and row["victim_side"] != side:
                continue
            if weapon and row["weapon"] != weapon:
                continue
            points.append(_point(row["victim_x"], row["victim_y"], metadata))
    elif heatmap_type == "path":
        for row in tables["ticks"]:
            if player and row["steam_id"] != player:
                continue
            if side and row["side"] != side:
                continue
            points.append(_point(row["x"], row["y"], metadata))
    elif heatmap_type in {"utility", "grenades"}:
        for row in tables["grenades"]:
            if player and row["thrower_steam_id"] != player:
                continue
            if side and row["thrower_side"] != side:
                continue
            if grenade_type and row["grenade_type"] != grenade_type:
                continue
            points.append(_point(row["x"], row["y"], metadata))
    else:
        raise ValueError("tipo de heatmap inválido")

    return {
        "match_id": match_id,
        "map": map_name,
        "type": heatmap_type,
        "points": points,
        "filters_applied": {
            "player": player,
            "team": team,
            "side": side,
            "round_range": round_range,
            "weapon": weapon,
            "grenade_type": grenade_type,
        },
    }


def _skip_player(
    steam_id: str,
    player: str | None,
    team: str | None,
    team_by_player: dict[str, str | None],
) -> bool:
    if player and steam_id != player:
        return True
    return bool(team and team_by_player.get(steam_id) != team)


def _point(x: float | None, y: float | None, metadata: RadarMetadata) -> dict[str, Any]:
    return {"x": x, "y": y, **world_to_radar(x, y, metadata), "weight": 1}
