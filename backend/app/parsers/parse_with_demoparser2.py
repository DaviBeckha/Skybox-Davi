"""Adapter demoparser2 -> `ParsedDemo` canônico do cs2-lab."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from app.parsers.normalize import (
    append_canonical,
    as_bomb_site,
    as_bool,
    as_float,
    as_int,
    as_str,
    as_winner,
    canonical_row,
    clean_steam,
    empty_tables,
    finalize,
    records,
    round_number,
    side_is_enemy,
    tick_time,
    value,
)
from app.parsers.result import ParsedDemo

# weapon_fire de granada => evento `thrown` (o contrato trata throws como weapon_fire).
WEAPON_TO_GRENADE = {
    "hegrenade": "he",
    "flashbang": "flash",
    "smokegrenade": "smoke",
    "molotov": "molotov",
    "incgrenade": "incendiary",
    "decoy": "decoy",
}


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

    # Rounds reais a partir de round_start/round_end (winner em maiúsculo no
    # demoparser2). Resolve a ausência de vencedor por round.
    round_starts: dict[int, int] = {}
    for row in _parse_event(parser, "round_start"):
        round_starts[round_number(row)] = as_int(value(row, "tick"), 0) or 0
    round_ends: dict[int, tuple[str, str, int]] = {}
    for row in _parse_event(parser, "round_end"):
        winner = as_winner(value(row, "winner"))
        if not winner:
            continue  # round 0 / warmup
        round_ends[round_number(row)] = (
            winner,
            as_str(value(row, "reason"), "") or "",
            as_int(value(row, "tick"), 0) or 0,
        )

    plant_by_round = {
        bomb["round_number"]: bomb
        for bomb in tables["bomb_events"]
        if bomb["event"] == "plant"
    }
    defuse_by_round = {
        bomb["round_number"]: bomb
        for bomb in tables["bomb_events"]
        if bomb["event"] == "defuse"
    }

    for rn in sorted(round_ends):
        winner, reason, end_tick = round_ends[rn]
        plant = plant_by_round.get(rn)
        defuse = defuse_by_round.get(rn)
        append_canonical(
            tables,
            "rounds",
            {
                "match_id": match_id,
                "round_number": rn,
                "winner": winner,
                "reason": reason,
                "start_tick": round_starts.get(rn, 0),
                "end_tick": end_tick,
                "bomb_planted": plant is not None,
                "bomb_site": as_bomb_site(plant["site"]) if plant else None,
                "plant_tick": plant["tick"] if plant else None,
                "defuse_tick": defuse["tick"] if defuse else None,
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


def extract_utility_events(
    demo_path: Path,
    *,
    match_id: str,
    tick_rate: int | None,
    side_of: Any,
    round_start_of: Any,
    parser_factory: ParserFactory | None = None,
) -> dict[str, list[dict]]:
    """Extrai granadas (thrown/detonate) e flashes (blinds) via demoparser2.

    Reusado pelo adapter awpy (que não expõe esses eventos discretos). `side_of`
    e `round_start_of` são callables que resolvem lado e tick inicial por round.
    """
    factory = parser_factory or _default_parser_factory
    parser = factory(str(demo_path))
    rate = tick_rate or 64
    grenades: list[dict] = []
    blinds: list[dict] = []

    def _time(rn: int, tick: int) -> float:
        return float(max(0, tick - round_start_of(rn)) / rate)

    for row in _parse_event(parser, "weapon_fire"):
        weapon = (as_str(value(row, "weapon", "weapon_name"), "") or "").replace("weapon_", "")
        grenade_type = WEAPON_TO_GRENADE.get(weapon)
        if grenade_type is None:
            continue
        rn = round_number(row)
        steam = clean_steam(value(row, "user_steamid", "steam_id"))
        tick = as_int(value(row, "tick"), 0) or 0
        grenades.append(
            canonical_row(
                "grenades",
                {
                    "match_id": match_id,
                    "round_number": rn,
                    "tick": tick,
                    "time": _time(rn, tick),
                    "thrower_steam_id": steam,
                    "thrower_side": side_of(rn, steam),
                    "grenade_type": grenade_type,
                    "event": "thrown",
                    "x": None,
                    "y": None,
                    "z": None,
                    "entity_id": None,
                },
            )
        )

    for event_name, grenade_type in (
        ("hegrenade_detonate", "he"),
        ("flashbang_detonate", "flash"),
        ("smokegrenade_detonate", "smoke"),
        ("inferno_startburn", "molotov"),
        ("decoy_detonate", "decoy"),
    ):
        for row in _parse_event(parser, event_name):
            rn = round_number(row)
            steam = clean_steam(value(row, "user_steamid", "steam_id"))
            tick = as_int(value(row, "tick"), 0) or 0
            grenades.append(
                canonical_row(
                    "grenades",
                    {
                        "match_id": match_id,
                        "round_number": rn,
                        "tick": tick,
                        "time": _time(rn, tick),
                        "thrower_steam_id": steam,
                        "thrower_side": side_of(rn, steam),
                        "grenade_type": grenade_type,
                        "event": "detonate",
                        "x": as_float(value(row, "x", "X")),
                        "y": as_float(value(row, "y", "Y")),
                        "z": as_float(value(row, "z", "Z")),
                        "entity_id": as_int(value(row, "entityid", "entity_id")),
                    },
                )
            )

    for row in _parse_event(parser, "player_blind"):
        rn = round_number(row)
        flasher = clean_steam(value(row, "attacker_steamid", "flasher_steam_id"))
        victim = clean_steam(value(row, "user_steamid", "victim_steam_id"))
        flasher_side = side_of(rn, flasher)
        victim_side = side_of(rn, victim)
        tick = as_int(value(row, "tick"), 0) or 0
        blinds.append(
            canonical_row(
                "blinds",
                {
                    "match_id": match_id,
                    "round_number": rn,
                    "tick": tick,
                    "time": _time(rn, tick),
                    "flasher_steam_id": flasher,
                    "victim_steam_id": victim,
                    "flasher_side": flasher_side,
                    "victim_side": victim_side,
                    "is_enemy": side_is_enemy(flasher_side, victim_side),
                    "duration": as_float(value(row, "blind_duration", "duration"), 0.0),
                    "entity_id": as_int(value(row, "entityid", "entity_id")),
                },
            )
        )

    return {"grenades": grenades, "blinds": blinds}
