"""Sucesso por bombsite."""

from __future__ import annotations

from typing import Any

from app.analytics.metrics import compute_bombsites
from app.analytics.reader import read_table


def build_bombsites(match_id: str, map_name: str) -> dict[str, Any]:
    result = compute_bombsites(read_table(match_id, "rounds"))
    return {
        "match_id": match_id,
        "map": map_name,
        "sites": result["sites"],
        "best_site_by_team": result["best_site_by_team"],
    }
