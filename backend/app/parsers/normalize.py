"""Normalização best-effort para adapters de parser de CS2.

Os parsers reais mudam nomes de colunas entre versões e nem sempre expõem todos
os campos. Este módulo converte dataframes/listas para o schema canônico do
cs2-lab, preservando nulos quando uma informação não está disponível.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.parsers.result import MatchMeta, ParsedDemo, PlayerMeta, RoundMeta
from app.parsers.schema import PARQUET_SCHEMAS


def records(source: Any) -> list[dict[str, Any]]:
    """Converte Polars/Pandas/list[dict]/None em lista de dicts."""
    if source is None:
        return []
    if hasattr(source, "to_dicts"):
        return list(source.to_dicts())
    if hasattr(source, "to_dict"):
        try:
            return list(source.to_dict("records"))
        except TypeError:
            data = source.to_dict()
            if isinstance(data, dict):
                keys = list(data)
                if not keys:
                    return []
                length = len(data[keys[0]])
                return [{key: data[key][idx] for key in keys} for idx in range(length)]
    if isinstance(source, list):
        return [dict(row) for row in source]
    if isinstance(source, tuple):
        return [dict(row) for row in source]
    return []


def value(row: dict[str, Any], *names: str, default: Any = None) -> Any:
    """Retorna a primeira coluna presente/não nula em `row`."""
    for name in names:
        if name in row and row[name] is not None:
            return row[name]
    return default


def as_int(raw: Any, default: int | None = None) -> int | None:
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def as_float(raw: Any, default: float | None = None) -> float | None:
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def as_bool(raw: Any, default: bool = False) -> bool:
    if raw is None:
        return default
    return bool(raw)


def as_str(raw: Any, default: str | None = None) -> str | None:
    if raw is None:
        return default
    return str(raw)


def as_weapon(raw: Any, default: str | None = None) -> str | None:
    """Normaliza o nome da arma: minúsculas e sem o prefixo `weapon_`.

    Os eventos do parser divergem (`kills` traz `ak47`, `weapon_fire` traz
    `weapon_ak47`); sem isso a mesma arma é contada duas vezes.
    """
    text = as_str(raw)
    if text is None:
        return default
    text = text.strip().lower()
    if text.startswith("weapon_"):
        text = text[len("weapon_") :]
    return text or default


def side_is_enemy(left: str | None, right: str | None) -> bool:
    return left in {"CT", "T"} and right in {"CT", "T"} and left != right


def as_side(raw: Any) -> str:
    """Normaliza um lado para `CT`/`T` (aceita minúsculas/variações); senão ``""``."""
    text = (as_str(raw, "") or "").strip().upper()
    if text in {"CT", "T"}:
        return text
    if text in {"COUNTER-TERRORIST", "COUNTERTERRORIST", "CTS"}:
        return "CT"
    if text in {"TERRORIST", "TERRORISTS", "TS"}:
        return "T"
    return ""


def as_winner(raw: Any) -> str:
    """Normaliza o vencedor do round para `CT`/`T` (aceita `ct`/`t`); senão ``""``."""
    text = (as_str(raw, "") or "").strip().upper()
    if text in {"CT", "T"}:
        return text
    if "CT" in text:
        return "CT"
    if text.startswith("T"):
        return "T"
    return ""


def as_bomb_site(raw: Any) -> str | None:
    """Normaliza o bombsite para `A`/`B`/None (mapeia `not_planted`, `BombsiteA`, etc.)."""
    text = (as_str(raw, "") or "").strip().upper()
    if not text or text in {"NOT_PLANTED", "NONE", "NULL"}:
        return None
    if text.endswith("A") or text == "A":
        return "A"
    if text.endswith("B") or text == "B":
        return "B"
    return text


def clean_steam(raw: Any) -> str | None:
    """steamID64 como string, ou None quando ausente/zero."""
    text = as_str(raw)
    if text is None or text in {"", "0"}:
        return None
    return text


def empty_tables() -> dict[str, list[dict]]:
    return {table: [] for table in PARQUET_SCHEMAS}


def canonical_row(table: str, row: dict[str, Any]) -> dict[str, Any]:
    """Filtra/ordena uma linha conforme o schema canônico da tabela."""
    return {column: row.get(column) for column in PARQUET_SCHEMAS[table]}


def append_canonical(tables: dict[str, list[dict]], table: str, row: dict[str, Any]) -> None:
    tables[table].append(canonical_row(table, row))


def round_number(row: dict[str, Any], default: int = 1) -> int:
    return (
        as_int(
            value(row, "round_number", "round_num", "round", "roundNumber"),
            default=default,
        )
        or default
    )


def tick_time(row: dict[str, Any], start_tick: int = 0, tick_rate: int | None = 64) -> float:
    raw = value(row, "time", "seconds", "game_time", "clock_time")
    if raw is not None:
        return as_float(raw, 0.0) or 0.0
    tick = as_int(value(row, "tick"), default=start_tick) or start_tick
    rate = tick_rate or 64
    return float(max(0, tick - start_tick) / rate)


def derive_players(
    tables: dict[str, list[dict]], team_a: str | None, team_b: str | None
) -> list[PlayerMeta]:
    """Monta roster a partir de players/ticks/eventos."""
    by_steam: dict[str, PlayerMeta] = {}
    for row in tables["players"]:
        steam_id = as_str(row.get("steam_id"))
        if not steam_id:
            continue
        by_steam[steam_id] = PlayerMeta(
            steam_id=steam_id,
            name=as_str(row.get("name"), steam_id) or steam_id,
            team=as_str(row.get("team"), "") or "",
            starting_side=as_str(row.get("starting_side"), "") or "",
        )

    for row in tables["ticks"]:
        steam_id = as_str(row.get("steam_id"))
        if not steam_id or steam_id in by_steam:
            continue
        side = as_str(row.get("side"), "") or ""
        team = as_str(row.get("team"))
        if team is None:
            team = team_a if side == "T" else team_b if side == "CT" else ""
        by_steam[steam_id] = PlayerMeta(
            steam_id=steam_id,
            name=as_str(row.get("name"), steam_id) or steam_id,
            team=team or "",
            starting_side=side,
        )

    for table, columns in {
        "kills": ("attacker_steam_id", "victim_steam_id"),
        "damages": ("attacker_steam_id", "victim_steam_id"),
        "shots": ("steam_id",),
        "bomb_events": ("steam_id",),
        "grenades": ("thrower_steam_id",),
        "blinds": ("flasher_steam_id", "victim_steam_id"),
    }.items():
        for row in tables[table]:
            for column in columns:
                steam_id = as_str(row.get(column))
                if steam_id and steam_id not in by_steam:
                    by_steam[steam_id] = PlayerMeta(steam_id, steam_id, "", "")

    players = sorted(by_steam.values(), key=lambda player: player.steam_id)
    tables["players"] = [
        canonical_row(
            "players",
            {
                "match_id": row.get("match_id"),
                "steam_id": player.steam_id,
                "name": player.name,
                "team": player.team,
                "starting_side": player.starting_side,
            },
        )
        for player in players
        for row in [tables["ticks"][0] if tables["ticks"] else {"match_id": ""}]
    ]
    return players


def derive_rounds(tables: dict[str, list[dict]], tick_rate: int | None) -> list[RoundMeta]:
    rounds: list[RoundMeta] = []
    for row in tables["rounds"]:
        rounds.append(
            RoundMeta(
                round_number=as_int(row.get("round_number"), 1) or 1,
                winner=as_str(row.get("winner"), "") or "",
                reason=as_str(row.get("reason"), "") or "",
                start_tick=as_int(row.get("start_tick"), 0) or 0,
                end_tick=as_int(row.get("end_tick"), 0) or 0,
            )
        )
    if rounds:
        return rounds

    event_rows: list[dict[str, Any]] = []
    for table in ("kills", "damages", "shots", "bomb_events", "grenades", "blinds", "ticks"):
        event_rows.extend(tables[table])
    if not event_rows:
        append_canonical(
            tables,
            "rounds",
            {
                "match_id": "",
                "round_number": 1,
                "winner": "",
                "reason": "",
                "start_tick": 0,
                "end_tick": 0,
                "bomb_planted": False,
                "bomb_site": None,
                "plant_tick": None,
                "defuse_tick": None,
                "t_team": "",
                "ct_team": "",
            },
        )
        return [RoundMeta(1, "", "", 0, 0)]

    by_round: dict[int, list[int]] = {}
    for row in event_rows:
        rn = round_number(row)
        tick = as_int(row.get("tick"), 0) or 0
        by_round.setdefault(rn, []).append(tick)
    for rn, ticks in sorted(by_round.items()):
        start = min(ticks)
        end = max(ticks)
        append_canonical(
            tables,
            "rounds",
            {
                "match_id": event_rows[0].get("match_id"),
                "round_number": rn,
                "winner": "",
                "reason": "",
                "start_tick": start,
                "end_tick": end,
                "bomb_planted": any(
                    e.get("round_number") == rn and e.get("event") == "plant"
                    for e in tables["bomb_events"]
                ),
                "bomb_site": next(
                    (
                        e.get("site")
                        for e in tables["bomb_events"]
                        if e.get("round_number") == rn and e.get("event") == "plant"
                    ),
                    None,
                ),
                "plant_tick": next(
                    (
                        e.get("tick")
                        for e in tables["bomb_events"]
                        if e.get("round_number") == rn and e.get("event") == "plant"
                    ),
                    None,
                ),
                "defuse_tick": next(
                    (
                        e.get("tick")
                        for e in tables["bomb_events"]
                        if e.get("round_number") == rn and e.get("event") == "defuse"
                    ),
                    None,
                ),
                "t_team": "",
                "ct_team": "",
            },
        )
        rounds.append(RoundMeta(rn, "", "", start, end))
    return rounds


def finalize(
    *,
    match_id: str,
    map_name: str,
    team_a: str | None,
    team_b: str | None,
    tick_rate: int | None,
    tables: dict[str, list[dict]],
) -> ParsedDemo:
    """Completa tabelas vazias, deriva roster/rounds e monta `ParsedDemo`."""
    for table in PARQUET_SCHEMAS:
        tables.setdefault(table, [])
        tables[table] = [canonical_row(table, row) for row in tables[table]]

    rounds = derive_rounds(tables, tick_rate)
    round_winners = {round_meta.round_number: round_meta.winner for round_meta in rounds}
    score_a = 0
    score_b = 0
    for rn, winner in round_winners.items():
        round_row = next((row for row in tables["rounds"] if row["round_number"] == rn), None)
        if round_row is None:
            continue
        t_team = round_row.get("t_team")
        ct_team = round_row.get("ct_team")
        winning_team = t_team if winner == "T" else ct_team if winner == "CT" else None
        if winning_team == team_a:
            score_a += 1
        elif winning_team == team_b:
            score_b += 1

    players = derive_players(tables, team_a, team_b)
    # `derive_players` preenche match_id a partir de ticks. Se não houver ticks,
    # garanta que a tabela ainda use o match_id atual.
    for row in tables["players"]:
        if not row.get("match_id"):
            row["match_id"] = match_id

    for table in PARQUET_SCHEMAS:
        for row in tables[table]:
            row["match_id"] = match_id

    return ParsedDemo(
        match=MatchMeta(
            map=map_name,
            team_a=team_a,
            team_b=team_b,
            score_a=score_a,
            score_b=score_b,
            tick_rate=tick_rate,
            started_at=None,
            players=players,
            rounds=rounds,
        ),
        tables=tables,
    )


def add_rows(
    tables: dict[str, list[dict]],
    table: str,
    match_id: str,
    source_rows: Iterable[dict[str, Any]],
) -> None:
    for row in source_rows:
        normalized = dict(row)
        normalized["match_id"] = match_id
        append_canonical(tables, table, normalized)
