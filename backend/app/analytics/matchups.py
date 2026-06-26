"""Kill matrix entre jogadores."""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.analytics.reader import read_tables


def build_matchups(match_id: str) -> dict[str, Any]:
    tables = read_tables(match_id, "players", "kills")
    matrix_counter: Counter[tuple[str, str]] = Counter()
    for kill in tables["kills"]:
        matrix_counter[(kill["attacker_steam_id"], kill["victim_steam_id"])] += 1
    return {
        "match_id": match_id,
        "players": [row["steam_id"] for row in tables["players"]],
        "matrix": [
            {
                "attacker_steam_id": attacker,
                "victim_steam_id": victim,
                "kills": kills,
            }
            for (attacker, victim), kills in sorted(matrix_counter.items())
        ],
    }
