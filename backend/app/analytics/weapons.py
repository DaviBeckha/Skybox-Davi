"""Estatísticas por arma e por jogador."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.analytics.reader import read_tables


def _ratio(num: float, den: float) -> float:
    return round(num / den, 4) if den else 0.0


def build_weapons(match_id: str) -> dict[str, Any]:
    tables = read_tables(match_id, "players", "shots", "damages", "kills")
    shots = defaultdict(int)
    hits = defaultdict(int)
    damage = defaultdict(int)
    kills = defaultdict(int)
    headshots = defaultdict(int)

    for row in tables["shots"]:
        shots[(row["steam_id"], row["weapon"])] += 1
    for row in tables["damages"]:
        key = (row["attacker_steam_id"], row["weapon"])
        hits[key] += 1
        damage[key] += int(row.get("hp_damage") or 0)
    for row in tables["kills"]:
        key = (row["attacker_steam_id"], row["weapon"])
        kills[key] += 1
        if row.get("headshot"):
            headshots[key] += 1

    payload_players = []
    for player in tables["players"]:
        steam_id = player["steam_id"]
        weapons = sorted(
            {
                weapon
                for sid, weapon in set(shots) | set(hits) | set(kills)
                if sid == steam_id and weapon
            }
        )
        weapon_rows = []
        total_shots = total_hits = total_damage = total_kills = total_hs = 0
        for weapon in weapons:
            key = (steam_id, weapon)
            weapon_shots = shots[key]
            weapon_hits = hits[key]
            weapon_damage = damage[key]
            weapon_kills = kills[key]
            weapon_hs = headshots[key]
            total_shots += weapon_shots
            total_hits += weapon_hits
            total_damage += weapon_damage
            total_kills += weapon_kills
            total_hs += weapon_hs
            weapon_rows.append(
                {
                    "weapon": weapon,
                    "shots": weapon_shots,
                    "hits": weapon_hits,
                    "accuracy": _ratio(weapon_hits, weapon_shots),
                    "kills": weapon_kills,
                    "headshots": weapon_hs,
                    "hs_pct": _ratio(weapon_hs, weapon_kills),
                    "damage": weapon_damage,
                    "damage_per_shot": _ratio(weapon_damage, weapon_shots),
                    "first_shot_accuracy": _ratio(weapon_hits, weapon_shots),
                }
            )
        payload_players.append(
            {
                "steam_id": steam_id,
                "name": player.get("name"),
                "weapons_used": weapons,
                "overall": {
                    "hs_pct": _ratio(total_hs, total_kills),
                    "accuracy": _ratio(total_hits, total_shots),
                    "damage_per_shot": _ratio(total_damage, total_shots),
                    "first_shot_accuracy": _ratio(total_hits, total_shots),
                },
                "weapons": weapon_rows,
            }
        )
    return {"match_id": match_id, "players": payload_players}
