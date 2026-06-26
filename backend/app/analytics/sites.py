"""Sucesso por bombsite."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.analytics.reader import read_table


def build_bombsites(match_id: str, map_name: str) -> dict[str, Any]:
    grouped: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {"plants": 0, "round_wins": 0}
    )
    for round_row in read_table(match_id, "rounds"):
        site = round_row.get("bomb_site")
        team = round_row.get("t_team")
        if not site or not team:
            continue
        item = grouped[(team, site)]
        item["plants"] += 1
        if round_row.get("winner") == "T":
            item["round_wins"] += 1

    sites = []
    best_by_team: dict[str, str] = {}
    for (team, site), item in sorted(grouped.items()):
        plants = item["plants"]
        wins = item["round_wins"]
        win_rate = round(wins / plants, 4) if plants else 0.0
        sites.append(
            {
                "team": team,
                "site": site,
                "plants": plants,
                "round_wins": wins,
                "win_rate": win_rate,
                "post_plant_win_rate": win_rate,
            }
        )
        current = best_by_team.get(team)
        if current is None or win_rate > next(
            row["win_rate"] for row in sites if row["team"] == team and row["site"] == current
        ):
            best_by_team[team] = site
    return {
        "match_id": match_id,
        "map": map_name,
        "sites": sites,
        "best_site_by_team": best_by_team,
    }
