"""Kill matrix (duelos): robustez a mortes sem atacante.

Mortes "do mundo" (bomba, queda, suicídio) chegam com `attacker_steam_id`
nulo. Antes do fix, isso fazia `sorted()` comparar `None` com `str` e o
endpoint `/stats/matchups` respondia 500 — a aba Duelos ficava vazia.
Usa apenas `tmp_data` (Parquet em tmp), sem PostgreSQL.
"""

from __future__ import annotations

import uuid

from app.analytics.matchups import build_matchups
from app.analytics.reader import match_dir
from app.parsers.schema import to_frame


def _write(match_id: str, table: str, rows: list[dict]) -> None:
    directory = match_dir(match_id)
    directory.mkdir(parents=True, exist_ok=True)
    to_frame(table, rows).write_parquet(directory / f"{table}.parquet")


def _player(match_id: str, steam_id: str, name: str, side: str) -> dict:
    return {
        "match_id": match_id,
        "steam_id": steam_id,
        "name": name,
        "team": f"team-{steam_id}",
        "starting_side": side,
    }


def _kill(match_id: str, attacker: str | None, victim: str, **over) -> dict:
    base = {
        "match_id": match_id,
        "round_number": 1,
        "tick": 100,
        "time": 1.0,
        "attacker_steam_id": attacker,
        "victim_steam_id": victim,
        "assister_steam_id": None,
        "weapon": "ak47",
        "headshot": False,
        "attacker_side": "T",
        "victim_side": "CT",
        "attacker_x": 0.0,
        "attacker_y": 0.0,
        "attacker_z": 0.0,
        "victim_x": 1.0,
        "victim_y": 1.0,
        "victim_z": 0.0,
    }
    base.update(over)
    return base


def test_build_matchups_ignores_kills_without_attacker(tmp_data) -> None:
    match_id = str(uuid.uuid4())
    _write(
        match_id,
        "players",
        [
            _player(match_id, "A", "Ana", "CT"),
            _player(match_id, "B", "Bia", "T"),
        ],
    )
    _write(
        match_id,
        "kills",
        [
            _kill(match_id, "A", "B", tick=100),
            _kill(match_id, "A", "B", tick=150),
            # morte sem atacante (bomba/queda/mundo): não é um duelo
            _kill(match_id, None, "A", tick=200, weapon="world", attacker_side=None),
        ],
    )

    # Antes do fix isto levantava TypeError (None < str) no sorted().
    result = build_matchups(match_id)

    assert result["players"] == ["A", "B"]
    pairs = {
        (entry["attacker_steam_id"], entry["victim_steam_id"]): entry["kills"]
        for entry in result["matrix"]
    }
    assert pairs == {("A", "B"): 2}
