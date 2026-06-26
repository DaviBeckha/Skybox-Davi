"""Métricas básicas por jogador."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.analytics.reader import read_tables


def _ratio(num: float, den: float) -> float:
    return round(num / den, 4) if den else 0.0


def build_player_stats(match_id: str) -> dict[str, Any]:
    tables = read_tables(match_id, "players", "kills", "damages", "rounds")
    players = tables["players"]
    rounds = tables["rounds"]
    round_count = max(1, len(rounds))
    kills_by_player: dict[str, list[dict]] = defaultdict(list)
    deaths_by_player: dict[str, list[dict]] = defaultdict(list)
    damage_by_player: dict[str, int] = defaultdict(int)
    assists_by_player: dict[str, int] = defaultdict(int)

    for kill in tables["kills"]:
        kills_by_player[kill["attacker_steam_id"]].append(kill)
        deaths_by_player[kill["victim_steam_id"]].append(kill)
        assister = kill.get("assister_steam_id")
        if assister:
            assists_by_player[assister] += 1
    for damage in tables["damages"]:
        damage_by_player[damage["attacker_steam_id"]] += int(damage.get("hp_damage") or 0)

    first_kills_by_round: dict[int, dict] = {}
    for kill in sorted(tables["kills"], key=lambda row: (row["round_number"], row["tick"])):
        first_kills_by_round.setdefault(kill["round_number"], kill)

    payload_players = []
    for player in players:
        steam_id = player["steam_id"]
        kill_rows = kills_by_player[steam_id]
        death_rows = deaths_by_player[steam_id]
        rounds_with_kill = {row["round_number"] for row in kill_rows}
        rounds_with_death = {row["round_number"] for row in death_rows}
        kast_rounds = len(rounds_with_kill | (set(range(1, round_count + 1)) - rounds_with_death))
        entry_attempts = [
            row
            for row in first_kills_by_round.values()
            if row["attacker_steam_id"] == steam_id or row["victim_steam_id"] == steam_id
        ]
        payload_players.append(
            {
                "steam_id": steam_id,
                "name": player.get("name"),
                "team": player.get("team"),
                "kills": len(kill_rows),
                "deaths": len(death_rows),
                "assists": assists_by_player[steam_id],
                "adr": round(damage_by_player[steam_id] / round_count, 2),
                "kast_pct": _ratio(kast_rounds, round_count),
                "entry_attempts": len(entry_attempts),
                "entry_kills": sum(
                    1 for row in entry_attempts if row["attacker_steam_id"] == steam_id
                ),
                "entry_deaths": sum(
                    1 for row in entry_attempts if row["victim_steam_id"] == steam_id
                ),
                "trade_kills": 0,
                "clutches": 0,
            }
        )
    return {"match_id": match_id, "players": payload_players}
