"""Adapter awpy -> `ParsedDemo` canônico do cs2-lab."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from app.parsers.normalize import (
    add_rows,
    append_canonical,
    as_bool,
    as_float,
    as_int,
    as_str,
    empty_tables,
    finalize,
    records,
    round_number,
    side_is_enemy,
    tick_time,
    value,
)
from app.parsers.result import ParsedDemo


class DemoFactory(Protocol):
    def __call__(self, path: str) -> Any: ...


def _default_demo_factory(path: str) -> Any:
    from awpy import Demo

    return Demo(path)


def _header_value(header: Any, *names: str, default: Any = None) -> Any:
    if isinstance(header, dict):
        return value(header, *names, default=default)
    for name in names:
        if hasattr(header, name):
            raw = getattr(header, name)
            if raw is not None:
                return raw
    return default


def _round_start_by_number(rounds: list[dict]) -> dict[int, int]:
    return {
        as_int(row.get("round_number"), 1) or 1: as_int(row.get("start_tick"), 0) or 0
        for row in rounds
    }


def parse_demo(
    demo_path: Path,
    *,
    match_id: str,
    demo_factory: DemoFactory | None = None,
) -> ParsedDemo:
    """Parseia uma `.dem` com awpy e converte para o contrato interno."""
    factory = demo_factory or _default_demo_factory
    demo = factory(str(demo_path))
    demo.parse()

    header = getattr(demo, "header", {}) or {}
    map_name = as_str(_header_value(header, "map_name", "map", "mapName"), "unknown") or "unknown"
    tick_rate = as_int(_header_value(header, "tick_rate", "tickrate"), 64)
    team_a = as_str(_header_value(header, "team_a", "teamA", "t_team_name", "team1"), "Team A")
    team_b = as_str(_header_value(header, "team_b", "teamB", "ct_team_name", "team2"), "Team B")

    tables = empty_tables()

    for row in records(getattr(demo, "rounds", None)):
        append_canonical(
            tables,
            "rounds",
            {
                "match_id": match_id,
                "round_number": round_number(row),
                "winner": as_str(value(row, "winner", "winning_side", "winner_side"), ""),
                "reason": as_str(value(row, "reason", "end_reason", "round_end_reason"), ""),
                "start_tick": as_int(value(row, "start_tick", "freeze_end_tick", "start"), 0),
                "end_tick": as_int(value(row, "end_tick", "end"), 0),
                "bomb_planted": as_bool(value(row, "bomb_planted", "has_bomb_plant"), False),
                "bomb_site": as_str(value(row, "bomb_site", "site", "plant_site")),
                "plant_tick": as_int(value(row, "plant_tick", "bomb_plant_tick")),
                "defuse_tick": as_int(value(row, "defuse_tick", "bomb_defuse_tick")),
                "t_team": as_str(value(row, "t_team", "team_t", "terrorist_team"), team_a),
                "ct_team": as_str(value(row, "ct_team", "team_ct", "ct_team_name"), team_b),
            },
        )
    round_starts = _round_start_by_number(tables["rounds"])

    for row in records(getattr(demo, "kills", None)):
        rn = round_number(row)
        append_canonical(
            tables,
            "kills",
            {
                "match_id": match_id,
                "round_number": rn,
                "tick": as_int(value(row, "tick"), 0),
                "time": tick_time(row, round_starts.get(rn, 0), tick_rate),
                "attacker_steam_id": as_str(
                    value(row, "attacker_steam_id", "attacker_steamid", "attacker_XUID"), ""
                ),
                "victim_steam_id": as_str(
                    value(row, "victim_steam_id", "victim_steamid", "victim_XUID"), ""
                ),
                "assister_steam_id": as_str(
                    value(row, "assister_steam_id", "assister_steamid", "assister_XUID")
                ),
                "weapon": as_str(value(row, "weapon", "weapon_name"), ""),
                "headshot": as_bool(value(row, "headshot", "is_headshot"), False),
                "attacker_side": as_str(
                    value(row, "attacker_side", "attacker_team_clan_name", "attacker_side"), ""
                ),
                "victim_side": as_str(
                    value(row, "victim_side", "victim_team_clan_name", "victim_side"), ""
                ),
                "attacker_x": as_float(value(row, "attacker_x", "attacker_X"), 0.0),
                "attacker_y": as_float(value(row, "attacker_y", "attacker_Y"), 0.0),
                "attacker_z": as_float(value(row, "attacker_z", "attacker_Z"), 0.0),
                "victim_x": as_float(value(row, "victim_x", "victim_X"), 0.0),
                "victim_y": as_float(value(row, "victim_y", "victim_Y"), 0.0),
                "victim_z": as_float(value(row, "victim_z", "victim_Z"), 0.0),
            },
        )

    for row in records(getattr(demo, "damages", None)):
        rn = round_number(row)
        append_canonical(
            tables,
            "damages",
            {
                "match_id": match_id,
                "round_number": rn,
                "tick": as_int(value(row, "tick"), 0),
                "time": tick_time(row, round_starts.get(rn, 0), tick_rate),
                "attacker_steam_id": as_str(
                    value(row, "attacker_steam_id", "attacker_steamid"), ""
                ),
                "victim_steam_id": as_str(value(row, "victim_steam_id", "victim_steamid"), ""),
                "weapon": as_str(value(row, "weapon", "weapon_name"), ""),
                "hp_damage": as_int(value(row, "hp_damage", "dmg_health", "health_damage"), 0),
                "armor_damage": as_int(value(row, "armor_damage", "dmg_armor"), 0),
                "hitgroup": as_str(value(row, "hitgroup", "hit_group"), ""),
            },
        )

    add_rows(tables, "shots", match_id, records(getattr(demo, "shots", None)))
    add_rows(tables, "bomb_events", match_id, records(getattr(demo, "bomb", None)))
    add_rows(tables, "grenades", match_id, records(getattr(demo, "grenades", None)))
    add_rows(tables, "blinds", match_id, records(getattr(demo, "blinds", None)))
    add_rows(tables, "ticks", match_id, records(getattr(demo, "ticks", None)))

    # Awpy nem sempre expõe `blinds` agregado; se existir `flashes`, aceite também.
    if not tables["blinds"]:
        for row in records(getattr(demo, "flashes", None)):
            flasher_side = as_str(value(row, "flasher_side"))
            victim_side = as_str(value(row, "victim_side"))
            append_canonical(
                tables,
                "blinds",
                {
                    "match_id": match_id,
                    "round_number": round_number(row),
                    "tick": as_int(value(row, "tick"), 0),
                    "time": tick_time(row, 0, tick_rate),
                    "flasher_steam_id": as_str(value(row, "flasher_steam_id", "attacker_steam_id")),
                    "victim_steam_id": as_str(value(row, "victim_steam_id", "player_steam_id"), ""),
                    "flasher_side": flasher_side,
                    "victim_side": victim_side,
                    "is_enemy": as_bool(
                        value(row, "is_enemy"), side_is_enemy(flasher_side, victim_side)
                    ),
                    "duration": as_float(value(row, "duration", "flash_duration"), 0.0),
                    "entity_id": as_int(value(row, "entity_id", "grenade_entity_id")),
                },
            )

    tables["replay_frames"] = list(tables["ticks"])
    return finalize(
        match_id=match_id,
        map_name=map_name,
        team_a=team_a,
        team_b=team_b,
        tick_rate=tick_rate,
        tables=tables,
    )
