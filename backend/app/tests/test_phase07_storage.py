"""Phase 07: storage analítico em Parquet + DuckDB.

Estes testes fixam o contrato de dados que parser real e mock devem produzir.
"""

from __future__ import annotations

import uuid

import polars as pl

from app.parsers.result import MatchMeta, ParsedDemo, PlayerMeta, RoundMeta
from app.parsers.schema import PARQUET_SCHEMAS
from app.storage.duckdb import refresh_views
from app.storage.parquet import write_parquet_tables


def _minimal_parsed_demo(match_id: str) -> ParsedDemo:
    player_a = PlayerMeta(
        steam_id="76561198000000001",
        name="alpha",
        team="Team A",
        starting_side="T",
    )
    player_b = PlayerMeta(
        steam_id="76561198000000002",
        name="bravo",
        team="Team B",
        starting_side="CT",
    )
    rows: dict[str, list[dict]] = {table: [] for table in PARQUET_SCHEMAS}
    rows["players"] = [
        {
            "match_id": match_id,
            "steam_id": player_a.steam_id,
            "name": player_a.name,
            "team": player_a.team,
            "starting_side": player_a.starting_side,
        },
        {
            "match_id": match_id,
            "steam_id": player_b.steam_id,
            "name": player_b.name,
            "team": player_b.team,
            "starting_side": player_b.starting_side,
        },
    ]
    rows["rounds"] = [
        {
            "match_id": match_id,
            "round_number": 1,
            "winner": "T",
            "reason": "bomb",
            "start_tick": 1000,
            "end_tick": 5000,
            "bomb_planted": True,
            "bomb_site": "A",
            "plant_tick": 3000,
            "defuse_tick": None,
            "t_team": "Team A",
            "ct_team": "Team B",
        }
    ]
    rows["shots"] = [
        {
            "match_id": match_id,
            "round_number": 1,
            "tick": 2500,
            "time": 23.4375,
            "steam_id": player_a.steam_id,
            "weapon": "ak47",
            "x": 10.0,
            "y": 20.0,
            "z": 0.0,
        }
    ]
    rows["grenades"] = [
        {
            "match_id": match_id,
            "round_number": 1,
            "tick": 2600,
            "time": 25.0,
            "thrower_steam_id": player_a.steam_id,
            "thrower_side": "T",
            "grenade_type": "flash",
            "event": "detonate",
            "x": 12.0,
            "y": 22.0,
            "z": 0.0,
            "entity_id": 7,
        }
    ]
    rows["blinds"] = [
        {
            "match_id": match_id,
            "round_number": 1,
            "tick": 2620,
            "time": 25.3125,
            "flasher_steam_id": player_a.steam_id,
            "victim_steam_id": player_b.steam_id,
            "flasher_side": "T",
            "victim_side": "CT",
            "is_enemy": True,
            "duration": 2.1,
            "entity_id": 7,
        }
    ]
    rows["ticks"] = [
        {
            "match_id": match_id,
            "round_number": 1,
            "tick": 2400,
            "time": 21.875,
            "steam_id": player_a.steam_id,
            "name": player_a.name,
            "side": "T",
            "x": 9.0,
            "y": 19.0,
            "z": 0.0,
            "yaw": 90.0,
            "hp": 100,
            "armor": 100,
            "weapon": "ak47",
            "alive": True,
        }
    ]
    rows["replay_frames"] = list(rows["ticks"])
    return ParsedDemo(
        match=MatchMeta(
            map="de_mirage",
            team_a="Team A",
            team_b="Team B",
            score_a=1,
            score_b=0,
            tick_rate=64,
            started_at=None,
            players=[player_a, player_b],
            rounds=[
                RoundMeta(
                    round_number=1,
                    winner="T",
                    reason="bomb",
                    start_tick=1000,
                    end_tick=5000,
                )
            ],
        ),
        tables=rows,
    )


def test_write_parquet_tables_uses_contract_schema_and_no_radar_columns(tmp_path) -> None:
    match_id = str(uuid.uuid4())
    parsed = _minimal_parsed_demo(match_id)

    match_dir = write_parquet_tables(match_id, parsed.tables, tmp_path)

    for table, schema in PARQUET_SCHEMAS.items():
        path = match_dir / f"{table}.parquet"
        assert path.exists(), table
        frame = pl.read_parquet(path)
        assert frame.columns == list(schema)
        assert "radar_x" not in frame.columns
        assert "radar_y" not in frame.columns


def test_duckdb_views_can_query_processed_parquet(tmp_path) -> None:
    match_id = str(uuid.uuid4())
    parsed = _minimal_parsed_demo(match_id)
    parquet_dir = tmp_path / "parquet"
    duckdb_path = tmp_path / "duckdb" / "cs2_lab.duckdb"
    write_parquet_tables(match_id, parsed.tables, parquet_dir)

    connection = refresh_views(parquet_dir, duckdb_path)
    try:
        shots = connection.execute("select count(*) from shots").fetchone()[0]
        rounds = connection.execute("select bomb_site, t_team, ct_team from rounds").fetchone()
    finally:
        connection.close()

    assert shots == 1
    assert rounds == ("A", "Team A", "Team B")
