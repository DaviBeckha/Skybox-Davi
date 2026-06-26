"""Adapter awpy -> `ParsedDemo` canônico do cs2-lab.

awpy fornece as tabelas estruturadas (rounds com winner, kills/damages/shots com
posições e side, ticks com side/round). Não expõe eventos discretos de granada
nem flashes, então `grenades`/`blinds` vêm do demoparser2 (híbrido).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Protocol

from app.parsers.normalize import (
    append_canonical,
    as_bomb_site,
    as_bool,
    as_float,
    as_int,
    as_side,
    as_str,
    as_weapon,
    as_winner,
    clean_steam,
    empty_tables,
    finalize,
    records,
    round_number,
    tick_time,
    value,
)
from app.parsers.result import ParsedDemo

logger = logging.getLogger("cs2-lab.parsers.awpy")


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


def _bomb_event(raw: Any) -> str:
    text = (as_str(raw, "") or "").strip().lower()
    if "plant" in text:
        return "plant"
    if "defus" in text:
        return "defuse"
    if "explod" in text or "detonate" in text:
        return "explode"
    return text


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

    # --- rounds (winner em minúsculo no awpy => normaliza) ---
    round_starts: dict[int, int] = {}
    for row in records(getattr(demo, "rounds", None)):
        rn = round_number(row)
        start_tick = as_int(value(row, "start", "start_tick", "freeze_end"), 0) or 0
        round_starts[rn] = start_tick
        plant_tick = as_int(value(row, "bomb_plant", "plant_tick", "bomb_plant_tick"))
        append_canonical(
            tables,
            "rounds",
            {
                "match_id": match_id,
                "round_number": rn,
                "winner": as_winner(value(row, "winner", "winning_side")),
                "reason": as_str(value(row, "reason", "end_reason"), ""),
                "start_tick": start_tick,
                "end_tick": as_int(value(row, "end", "end_tick", "official_end"), 0),
                "bomb_planted": plant_tick is not None,
                "bomb_site": as_bomb_site(value(row, "bomb_site", "site", "plant_site")),
                "plant_tick": plant_tick,
                "defuse_tick": as_int(value(row, "defuse_tick", "bomb_defuse_tick")),
                "t_team": as_str(value(row, "t_team", "team_t"), team_a),
                "ct_team": as_str(value(row, "ct_team", "team_ct"), team_b),
            },
        )

    def round_start_of(rn: int) -> int:
        return round_starts.get(rn, 0)

    # --- ticks (X/Y/Z, side, round_num; sem yaw/armor/weapon/alive no awpy) ---
    side_by_round_steam: dict[tuple[int, str], str] = {}
    side_by_steam: dict[str, str] = {}
    team_name_by_steam: dict[str, str] = {}
    for row in records(getattr(demo, "ticks", None)):
        rn = round_number(row)
        steam = clean_steam(value(row, "steamid", "steam_id"))
        side = as_side(value(row, "side", "team_side"))
        hp = as_int(value(row, "health", "hp"), 0) or 0
        if steam and side:
            side_by_round_steam[(rn, steam)] = side
            side_by_steam.setdefault(steam, side)
        clan = as_str(value(row, "team_clan_name", "team_name", "clan_name"))
        if steam and clan and steam not in team_name_by_steam:
            team_name_by_steam[steam] = clan
        append_canonical(
            tables,
            "ticks",
            {
                "match_id": match_id,
                "round_number": rn,
                "tick": as_int(value(row, "tick"), 0),
                "time": tick_time(row, round_start_of(rn), tick_rate),
                "steam_id": steam,
                "name": as_str(value(row, "name"), ""),
                "side": side,
                "x": as_float(value(row, "X", "x"), 0.0),
                "y": as_float(value(row, "Y", "y"), 0.0),
                "z": as_float(value(row, "Z", "z"), 0.0),
                "yaw": as_float(value(row, "yaw", "view_yaw")),
                "hp": hp,
                "armor": as_int(value(row, "armor", "armor_value")),
                "weapon": as_weapon(value(row, "active_weapon", "weapon")),
                "alive": as_bool(value(row, "is_alive", "alive"), hp > 0),
            },
        )

    def side_of(rn: int, steam: str | None) -> str:
        if not steam:
            return ""
        return side_by_round_steam.get((rn, steam)) or side_by_steam.get(steam, "")

    # --- times fixos por roster + troca de lado por round ---
    # Os times são conjuntos fixos de jogadores; o LADO (T/CT) troca no intervalo.
    # Contar o placar por lado dá totais impossíveis (ex.: 18 num MR12); por isso
    # derivamos, round a round, qual time está em cada lado a partir dos ticks.
    rounds_seen = sorted({rn for (rn, _steam) in side_by_round_steam})
    first_round = rounds_seen[0] if rounds_seen else 1
    first_sides = {
        steam: side
        for (rn, steam), side in side_by_round_steam.items()
        if rn == first_round
    }
    team_t_roster = {s for s, side in first_sides.items() if side == "T"}
    team_ct_roster = {s for s, side in first_sides.items() if side == "CT"}

    def _team_label(roster: set[str], fallback: str) -> str:
        for steam in roster:
            name = team_name_by_steam.get(steam)
            if name:
                return name
        return fallback

    team_a = _team_label(team_t_roster, team_a)  # time que começou no lado T
    team_b = _team_label(team_ct_roster, team_b)  # time que começou no lado CT

    def _round_teams(rn: int) -> tuple[str, str]:
        """(t_team, ct_team) do round, pelo lado majoritário do roster que começou T."""
        t_votes = sum(1 for s in team_t_roster if side_by_round_steam.get((rn, s)) == "T")
        ct_votes = sum(1 for s in team_t_roster if side_by_round_steam.get((rn, s)) == "CT")
        if t_votes == 0 and ct_votes == 0:
            a_on_t = ((rn - first_round) // 12) % 2 == 0  # fallback: troca a cada 12
        else:
            a_on_t = t_votes >= ct_votes
        return (team_a, team_b) if a_on_t else (team_b, team_a)

    for round_row in tables["rounds"]:
        t_label, ct_label = _round_teams(round_row["round_number"])
        round_row["t_team"] = t_label
        round_row["ct_team"] = ct_label

    # --- kills (com posições e side) ---
    for row in records(getattr(demo, "kills", None)):
        rn = round_number(row)
        append_canonical(
            tables,
            "kills",
            {
                "match_id": match_id,
                "round_number": rn,
                "tick": as_int(value(row, "tick"), 0),
                "time": tick_time(row, round_start_of(rn), tick_rate),
                "attacker_steam_id": clean_steam(value(row, "attacker_steamid")),
                "victim_steam_id": clean_steam(value(row, "victim_steamid")),
                "assister_steam_id": clean_steam(value(row, "assister_steamid")),
                "weapon": as_weapon(value(row, "weapon", "weapon_name"), ""),
                "headshot": as_bool(value(row, "headshot", "is_headshot"), False),
                "attacker_side": as_side(value(row, "attacker_side")),
                "victim_side": as_side(value(row, "victim_side")),
                "attacker_x": as_float(value(row, "attacker_X", "attacker_x"), 0.0),
                "attacker_y": as_float(value(row, "attacker_Y", "attacker_y"), 0.0),
                "attacker_z": as_float(value(row, "attacker_Z", "attacker_z"), 0.0),
                "victim_x": as_float(value(row, "victim_X", "victim_x"), 0.0),
                "victim_y": as_float(value(row, "victim_Y", "victim_y"), 0.0),
                "victim_z": as_float(value(row, "victim_Z", "victim_z"), 0.0),
            },
        )

    # --- damages ---
    for row in records(getattr(demo, "damages", None)):
        rn = round_number(row)
        append_canonical(
            tables,
            "damages",
            {
                "match_id": match_id,
                "round_number": rn,
                "tick": as_int(value(row, "tick"), 0),
                "time": tick_time(row, round_start_of(rn), tick_rate),
                "attacker_steam_id": clean_steam(value(row, "attacker_steamid")),
                "victim_steam_id": clean_steam(value(row, "victim_steamid")),
                "weapon": as_weapon(value(row, "weapon", "weapon_name"), ""),
                "hp_damage": as_int(value(row, "dmg_health", "hp_damage", "dmg_health_real"), 0),
                "armor_damage": as_int(value(row, "dmg_armor", "armor_damage"), 0),
                "hitgroup": as_str(value(row, "hitgroup", "hit_group"), ""),
            },
        )

    # --- shots (weapon_fire; inclui throws de granada, conforme o contrato) ---
    for row in records(getattr(demo, "shots", None)):
        rn = round_number(row)
        append_canonical(
            tables,
            "shots",
            {
                "match_id": match_id,
                "round_number": rn,
                "tick": as_int(value(row, "tick"), 0),
                "time": tick_time(row, round_start_of(rn), tick_rate),
                "steam_id": clean_steam(value(row, "player_steamid", "steamid", "user_steamid")),
                "weapon": as_weapon(value(row, "weapon", "weapon_name"), ""),
                "x": as_float(value(row, "player_X", "X", "x"), 0.0),
                "y": as_float(value(row, "player_Y", "Y", "y"), 0.0),
                "z": as_float(value(row, "player_Z", "Z", "z"), 0.0),
            },
        )

    # --- bomb_events ---
    for row in records(getattr(demo, "bomb", None)):
        rn = round_number(row)
        append_canonical(
            tables,
            "bomb_events",
            {
                "match_id": match_id,
                "round_number": rn,
                "tick": as_int(value(row, "tick"), 0),
                "time": tick_time(row, round_start_of(rn), tick_rate),
                "event": _bomb_event(value(row, "event")),
                "steam_id": clean_steam(value(row, "steamid", "user_steamid")),
                "site": as_bomb_site(value(row, "bombsite", "site")),
                "x": as_float(value(row, "X", "x")),
                "y": as_float(value(row, "Y", "y")),
                "z": as_float(value(row, "Z", "z")),
            },
        )

    # --- grenades + blinds via demoparser2 (awpy não expõe esses eventos) ---
    _supplement_utility(
        demo_path,
        match_id=match_id,
        tick_rate=tick_rate,
        side_of=side_of,
        round_start_of=round_start_of,
        tables=tables,
    )

    # replay_frames = downsample de ticks (1 a cada ~8 ticks).
    step = max(1, (tick_rate or 64) // 8)
    tables["replay_frames"] = [row for row in tables["ticks"] if (row["tick"] or 0) % step == 0]

    return finalize(
        match_id=match_id,
        map_name=map_name,
        team_a=team_a,
        team_b=team_b,
        tick_rate=tick_rate,
        tables=tables,
    )


def _supplement_utility(
    demo_path: Path,
    *,
    match_id: str,
    tick_rate: int | None,
    side_of: Any,
    round_start_of: Any,
    tables: dict[str, list[dict]],
) -> None:
    """Preenche grenades/blinds via demoparser2; falha aqui não derruba o parse."""
    try:
        import importlib.util

        if importlib.util.find_spec("demoparser2") is None:
            return
        from app.parsers.parse_with_demoparser2 import extract_utility_events

        utility = extract_utility_events(
            demo_path,
            match_id=match_id,
            tick_rate=tick_rate,
            side_of=side_of,
            round_start_of=round_start_of,
        )
        tables["grenades"] = utility["grenades"]
        tables["blinds"] = utility["blinds"]
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException as exc:  # noqa: BLE001 - utility é best-effort
        logger.warning("Falha ao extrair granadas/flashes via demoparser2: %s", exc)
