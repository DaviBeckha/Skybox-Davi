"""Economia por round e por jogador."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from app.analytics.reader import read_tables


def build_economy(match_id: str) -> dict[str, Any]:
    tables = read_tables(match_id, "economy", "rounds")
    economy = tables["economy"]
    rounds_payload = []
    for round_row in tables["rounds"]:
        rn = round_row["round_number"]
        t_rows = [row for row in economy if row["round_number"] == rn and row["side"] == "T"]
        ct_rows = [row for row in economy if row["round_number"] == rn and row["side"] == "CT"]
        rounds_payload.append(
            {
                "round_number": rn,
                "t_team": round_row.get("t_team"),
                "ct_team": round_row.get("ct_team"),
                "t_buy": _most_common_buy(t_rows),
                "ct_buy": _most_common_buy(ct_rows),
                "t_equip_value": _avg_int(t_rows, "equip_value"),
                "ct_equip_value": _avg_int(ct_rows, "equip_value"),
            }
        )

    by_player_rows = []
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in economy:
        grouped[row["steam_id"]].append(row)
    for steam_id, rows in sorted(grouped.items()):
        buy_counts = Counter(row.get("buy_type") for row in rows)
        by_player_rows.append(
            {
                "steam_id": steam_id,
                "avg_equip_value": _avg_int(rows, "equip_value"),
                "eco_rounds": buy_counts["eco"],
                "force_rounds": buy_counts["force"],
                "full_rounds": buy_counts["full"],
            }
        )
    return {"match_id": match_id, "rounds": rounds_payload, "by_player": by_player_rows}


def _avg_int(rows: list[dict], column: str) -> int | None:
    values = [int(row[column]) for row in rows if row.get(column) is not None]
    return round(sum(values) / len(values)) if values else None


def _most_common_buy(rows: list[dict]) -> str | None:
    values = [row.get("buy_type") for row in rows if row.get("buy_type")]
    if not values:
        return None
    return Counter(values).most_common(1)[0][0]
