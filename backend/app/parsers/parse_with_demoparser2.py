"""Adapter demoparser2 -> `ParsedDemo` canônico do cs2-lab."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from app.parsers.normalize import (
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


class ParserFactory(Protocol):
    def __call__(self, path: str) -> Any: ...


def _default_parser_factory(path: str) -> Any:
    from demoparser2 import DemoParser

    return DemoParser(path)


def _parse_event(parser: Any, event_name: str) -> list[dict]:
    if not hasattr(parser, "parse_event"):
        return []
    try:
        return records(parser.parse_event(event_name))
    except Exception:  # noqa: BLE001 - eventos ausentes variam entre versões
        return []


def _parse_ticks(parser: Any) -> list[dict]:
    if not hasattr(parser, "parse_ticks"):
        return []
    wanted = [
        "X",
        "Y",
        "Z",
        "x",
        "y",
        "z",
        "yaw",
        "health",
        "armor_value",
        "active_weapon_name",
        "is_alive",
        "side",
        "team_name",
        "name",
        "steamid",
    ]
    try:
        return records(parser.parse_ticks(wanted))
    except TypeError:
        return records(parser.parse_ticks())


def _header(parser: Any, *names: str, default: Any = None) -> Any:
    header = getattr(parser, "header", {}) or {}
    if isinstance(header, dict):
        for name in names:
            if name in header and header[name] is not None:
                return header[name]
    for name in names:
        if hasattr(parser, name):
            raw = getattr(parser, name)
            if raw is not None:
                return raw
    return default


def parse_demo(
    demo_path: Path,
    *,
    match_id: str,
    parser_factory: ParserFactory | None = None,
) -> ParsedDemo:
    """Parseia uma `.dem` com demoparser2 e converte para o contrato interno."""
    factory = parser_factory or _default_parser_factory
    parser = factory(str(demo_path))
    map_name = as_str(_header(parser, "map_name", "map", default="unknown"), "unknown") or "unknown"
    tick_rate = as_int(_header(parser, "tick_rate", "tickrate", default=64), 64)
    team_a = "Team A"
    team_b = "Team B"
    tables = empty_tables()

    tick_rows = _parse_ticks(parser)
    for row in tick_rows:
        side = as_str(value(row, "side", "team_side"), "")
        team = as_str(value(row, "team", "team_name"), "")
        if side == "T" and team:
            team_a = team
        if side == "CT" and team:
            team_b = team
        append_canonical(
            tables,
            "ticks",
            {
                "match_id": match_id,
                "round_number": round_number(row),
                "tick": as_int(value(row, "tick"), 0),
                "time": tick_time(row, 0, tick_rate),
                "steam_id": as_str(value(row, "steam_id", "steamid"), ""),
                "name": as_str(value(row, "name"), ""),
                "side": side,
                "x": as_float(value(row, "x", "X"), 0.0),
                "y": as_float(value(row, "y", "Y"), 0.0),
                "z": as_float(value(row, "z", "Z"), 0.0),
                "yaw": as_float(value(row, "yaw", "view_yaw")),
                "hp": as_int(value(row, "hp", "health"), 0),
                "armor": as_int(value(row, "armor", "armor_value"), 0),
                "weapon": as_str(value(row, "weapon", "active_weapon_name"), ""),
                "alive": as_bool(value(row, "alive", "is_alive"), True),
                "team": team,
            },
        )

    for row in _parse_event(parser, "player_death"):
        rn = round_number(row)
        append_canonical(
            tables,
            "kills",
            {
                "match_id": match_id,
                "round_number": rn,
                "tick": as_int(value(row, "tick"), 0),
                "time": tick_time(row, 0, tick_rate),
                "attacker_steam_id": as_str(
                    value(row, "attacker_steam_id", "attacker_steamid"), ""
                ),
                "victim_steam_id": as_str(value(row, "victim_steam_id", "victim_steamid"), ""),
                "assister_steam_id": as_str(value(row, "assister_steam_id", "assister_steamid")),
                "weapon": as_str(value(row, "weapon", "weapon_name"), ""),
                "headshot": as_bool(value(row, "headshot"), False),
                "attacker_side": as_str(value(row, "attacker_side"), ""),
                "victim_side": as_str(value(row, "victim_side"), ""),
                "attacker_x": as_float(value(row, "attacker_x"), 0.0),
                "attacker_y": as_float(value(row, "attacker_y"), 0.0),
                "attacker_z": as_float(value(row, "attacker_z"), 0.0),
                "victim_x": as_float(value(row, "victim_x"), 0.0),
                "victim_y": as_float(value(row, "victim_y"), 0.0),
                "victim_z": as_float(value(row, "victim_z"), 0.0),
            },
        )

    for row in _parse_event(parser, "player_hurt"):
        append_canonical(
            tables,
            "damages",
            {
                "match_id": match_id,
                "round_number": round_number(row),
                "tick": as_int(value(row, "tick"), 0),
                "time": tick_time(row, 0, tick_rate),
                "attacker_steam_id": as_str(
                    value(row, "attacker_steam_id", "attacker_steamid"), ""
                ),
                "victim_steam_id": as_str(value(row, "victim_steam_id", "victim_steamid"), ""),
                "weapon": as_str(value(row, "weapon", "weapon_name"), ""),
                "hp_damage": as_int(value(row, "hp_damage", "dmg_health"), 0),
                "armor_damage": as_int(value(row, "armor_damage", "dmg_armor"), 0),
                "hitgroup": as_str(value(row, "hitgroup"), ""),
            },
        )

    for row in _parse_event(parser, "weapon_fire"):
        append_canonical(
            tables,
            "shots",
            {
                "match_id": match_id,
                "round_number": round_number(row),
                "tick": as_int(value(row, "tick"), 0),
                "time": tick_time(row, 0, tick_rate),
                "steam_id": as_str(value(row, "steam_id", "user_steamid"), ""),
                "weapon": as_str(value(row, "weapon", "weapon_name"), ""),
                "x": as_float(value(row, "x", "X"), 0.0),
                "y": as_float(value(row, "y", "Y"), 0.0),
                "z": as_float(value(row, "z", "Z"), 0.0),
            },
        )

    for event_name, event_value in (
        ("bomb_planted", "plant"),
        ("bomb_defused", "defuse"),
        ("bomb_exploded", "explode"),
    ):
        for row in _parse_event(parser, event_name):
            append_canonical(
                tables,
                "bomb_events",
                {
                    "match_id": match_id,
                    "round_number": round_number(row),
                    "tick": as_int(value(row, "tick"), 0),
                    "time": tick_time(row, 0, tick_rate),
                    "event": event_value,
                    "steam_id": as_str(value(row, "steam_id", "user_steamid")),
                    "site": as_str(value(row, "site", "bomb_site")),
                    "x": as_float(value(row, "x", "X")),
                    "y": as_float(value(row, "y", "Y")),
                    "z": as_float(value(row, "z", "Z")),
                },
            )

    for event_name, grenade_type in (
        ("hegrenade_detonate", "he"),
        ("flashbang_detonate", "flash"),
        ("smokegrenade_detonate", "smoke"),
        ("molotov_detonate", "molotov"),
        ("inferno_startburn", "molotov"),
        ("decoy_detonate", "decoy"),
    ):
        for row in _parse_event(parser, event_name):
            append_canonical(
                tables,
                "grenades",
                {
                    "match_id": match_id,
                    "round_number": round_number(row),
                    "tick": as_int(value(row, "tick"), 0),
                    "time": tick_time(row, 0, tick_rate),
                    "thrower_steam_id": as_str(value(row, "thrower_steam_id", "user_steamid"), ""),
                    "thrower_side": as_str(value(row, "thrower_side"), ""),
                    "grenade_type": grenade_type,
                    "event": "detonate",
                    "x": as_float(value(row, "x", "X"), 0.0),
                    "y": as_float(value(row, "y", "Y"), 0.0),
                    "z": as_float(value(row, "z", "Z"), 0.0),
                    "entity_id": as_int(value(row, "entity_id", "entityid")),
                },
            )

    for row in _parse_event(parser, "player_blind"):
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
                "victim_steam_id": as_str(value(row, "victim_steam_id", "user_steamid"), ""),
                "flasher_side": flasher_side,
                "victim_side": victim_side,
                "is_enemy": as_bool(
                    value(row, "is_enemy"), side_is_enemy(flasher_side, victim_side)
                ),
                "duration": as_float(value(row, "duration", "blind_duration"), 0.0),
                "entity_id": as_int(value(row, "entity_id", "entityid")),
            },
        )

    tables["replay_frames"] = list(tables["ticks"])
    for bomb in tables["bomb_events"]:
        if bomb["event"] == "plant":
            append_canonical(
                tables,
                "rounds",
                {
                    "match_id": match_id,
                    "round_number": bomb["round_number"],
                    "winner": "",
                    "reason": "bomb",
                    "start_tick": 0,
                    "end_tick": max([tick["tick"] for tick in tables["ticks"]] or [bomb["tick"]]),
                    "bomb_planted": True,
                    "bomb_site": bomb["site"],
                    "plant_tick": bomb["tick"],
                    "defuse_tick": None,
                    "t_team": team_a,
                    "ct_team": team_b,
                },
            )

    return finalize(
        match_id=match_id,
        map_name=map_name,
        team_a=team_a,
        team_b=team_b,
        tick_rate=tick_rate,
        tables=tables,
    )
