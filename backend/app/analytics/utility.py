"""Métricas de utilidade: granadas, dano e flashes."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.analytics.reader import read_tables

# Chaves do payload (contrato seção 4). `incendiary` é agrupado em `molotov`
# (ambos são granadas de fogo; o dano de fogo também é somado em molotov).
_GRENADE_KEYS = ("he", "flash", "smoke", "molotov", "decoy")
_TYPE_ALIASES = {"incendiary": "molotov"}


def build_utility(match_id: str) -> dict[str, Any]:
    tables = read_tables(match_id, "players", "grenades", "blinds", "damages", "kills")
    by_player: dict[str, dict[str, Any]] = {}
    for player in tables["players"]:
        by_player[player["steam_id"]] = {
            "steam_id": player["steam_id"],
            "name": player.get("name"),
            "grenades_thrown": {key: 0 for key in (*_GRENADE_KEYS, "total")},
            "he_with_damage": 0,
            "he_damage_total": 0,
            "molotov_damage_total": 0,
            "flashes_thrown": 0,
            "enemies_blinded": 0,
            "enemy_blind_time": 0.0,
            "flash_assists": 0,
            "utility_damage": 0,
        }

    flash_entities_by_player: dict[str, set[int]] = defaultdict(set)
    for grenade in tables["grenades"]:
        if grenade.get("event") != "thrown":
            continue
        steam_id = grenade.get("thrower_steam_id")
        if steam_id not in by_player:
            continue
        grenade_type = grenade.get("grenade_type")
        key = _TYPE_ALIASES.get(grenade_type, grenade_type)
        if key in _GRENADE_KEYS:
            by_player[steam_id]["grenades_thrown"][key] += 1
            by_player[steam_id]["grenades_thrown"]["total"] += 1
        if grenade_type == "flash":
            by_player[steam_id]["flashes_thrown"] += 1
            if grenade.get("entity_id") is not None:
                flash_entities_by_player[steam_id].add(grenade["entity_id"])

    he_damage_events: dict[str, set[tuple[int, int]]] = defaultdict(set)
    for damage in tables["damages"]:
        steam_id = damage.get("attacker_steam_id")
        if steam_id not in by_player:
            continue
        weapon = damage.get("weapon")
        amount = int(damage.get("hp_damage") or 0)
        if weapon == "hegrenade":
            by_player[steam_id]["he_damage_total"] += amount
            by_player[steam_id]["utility_damage"] += amount
            he_damage_events[steam_id].add((damage["round_number"], damage["tick"]))
        if weapon in {"molotov", "incgrenade", "inferno"}:
            by_player[steam_id]["molotov_damage_total"] += amount
            by_player[steam_id]["utility_damage"] += amount
    for steam_id, events in he_damage_events.items():
        by_player[steam_id]["he_with_damage"] = len(events)

    kills_by_victim_round = defaultdict(list)
    for kill in tables["kills"]:
        kills_by_victim_round[(kill["victim_steam_id"], kill["round_number"])].append(kill)

    for blind in tables["blinds"]:
        flasher = blind.get("flasher_steam_id")
        if flasher not in by_player or not blind.get("is_enemy"):
            continue
        by_player[flasher]["enemies_blinded"] += 1
        by_player[flasher]["enemy_blind_time"] += float(blind.get("duration") or 0.0)
        for kill in kills_by_victim_round[(blind["victim_steam_id"], blind["round_number"])]:
            if kill["tick"] >= blind["tick"]:
                by_player[flasher]["flash_assists"] += 1
                break

    for item in by_player.values():
        item["enemy_blind_time"] = round(item["enemy_blind_time"], 2)
    return {"match_id": match_id, "players": list(by_player.values())}
