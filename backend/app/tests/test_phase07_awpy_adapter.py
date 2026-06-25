"""Phase 07: adapter awpy -> schema canônico do cs2-lab."""

from __future__ import annotations

import uuid
from pathlib import Path

import polars as pl

from app.parsers.parse_with_awpy import parse_demo
from app.parsers.schema import PARQUET_SCHEMAS


class _FakeAwpyDemo:
    def __init__(self, _path: str) -> None:
        self.header = {
            "map_name": "de_mirage",
            "tick_rate": 64,
            "team_a": "Team A",
            "team_b": "Team B",
        }

    def parse(self) -> None:
        self.rounds = pl.DataFrame(
            [
                {
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
        )
        self.kills = pl.DataFrame(
            [
                {
                    "round_number": 1,
                    "tick": 3500,
                    "time": 39.0625,
                    "attacker_steam_id": "76561198000000001",
                    "victim_steam_id": "76561198000000002",
                    "assister_steam_id": None,
                    "weapon": "ak47",
                    "headshot": True,
                    "attacker_side": "T",
                    "victim_side": "CT",
                    "attacker_x": 10.0,
                    "attacker_y": 20.0,
                    "attacker_z": 0.0,
                    "victim_x": 30.0,
                    "victim_y": 40.0,
                    "victim_z": 0.0,
                }
            ]
        )
        self.damages = pl.DataFrame(
            [
                {
                    "round_number": 1,
                    "tick": 3400,
                    "time": 37.5,
                    "attacker_steam_id": "76561198000000001",
                    "victim_steam_id": "76561198000000002",
                    "weapon": "ak47",
                    "hp_damage": 100,
                    "armor_damage": 12,
                    "hitgroup": "head",
                }
            ]
        )
        self.shots = pl.DataFrame(
            [
                {
                    "round_number": 1,
                    "tick": 3300,
                    "time": 35.9375,
                    "steam_id": "76561198000000001",
                    "weapon": "ak47",
                    "x": 10.0,
                    "y": 20.0,
                    "z": 0.0,
                }
            ]
        )
        self.bomb = pl.DataFrame(
            [
                {
                    "round_number": 1,
                    "tick": 3000,
                    "time": 31.25,
                    "event": "plant",
                    "steam_id": "76561198000000001",
                    "site": "A",
                    "x": 50.0,
                    "y": 60.0,
                    "z": 0.0,
                }
            ]
        )
        self.grenades = pl.DataFrame(
            [
                {
                    "round_number": 1,
                    "tick": 2600,
                    "time": 25.0,
                    "thrower_steam_id": "76561198000000001",
                    "thrower_side": "T",
                    "grenade_type": "flash",
                    "event": "detonate",
                    "x": 12.0,
                    "y": 22.0,
                    "z": 0.0,
                    "entity_id": 7,
                }
            ]
        )
        self.blinds = pl.DataFrame(
            [
                {
                    "round_number": 1,
                    "tick": 2620,
                    "time": 25.3125,
                    "flasher_steam_id": "76561198000000001",
                    "victim_steam_id": "76561198000000002",
                    "flasher_side": "T",
                    "victim_side": "CT",
                    "is_enemy": True,
                    "duration": 2.1,
                    "entity_id": 7,
                }
            ]
        )
        self.ticks = pl.DataFrame(
            [
                {
                    "round_number": 1,
                    "tick": 2400,
                    "time": 21.875,
                    "steam_id": "76561198000000001",
                    "name": "alpha",
                    "side": "T",
                    "team": "Team A",
                    "x": 9.0,
                    "y": 19.0,
                    "z": 0.0,
                    "yaw": 90.0,
                    "hp": 100,
                    "armor": 100,
                    "weapon": "ak47",
                    "alive": True,
                },
                {
                    "round_number": 1,
                    "tick": 2400,
                    "time": 21.875,
                    "steam_id": "76561198000000002",
                    "name": "bravo",
                    "side": "CT",
                    "team": "Team B",
                    "x": 29.0,
                    "y": 39.0,
                    "z": 0.0,
                    "yaw": 270.0,
                    "hp": 100,
                    "armor": 100,
                    "weapon": "m4a1",
                    "alive": True,
                },
            ]
        )


def test_awpy_adapter_maps_demo_frames_to_contract_schema() -> None:
    match_id = str(uuid.uuid4())

    parsed = parse_demo(
        Path("fixture.dem"),
        match_id=match_id,
        demo_factory=_FakeAwpyDemo,
    )

    assert parsed.match.map == "de_mirage"
    assert parsed.match.team_a == "Team A"
    assert parsed.match.team_b == "Team B"
    assert parsed.match.tick_rate == 64
    assert [p.steam_id for p in parsed.match.players] == [
        "76561198000000001",
        "76561198000000002",
    ]
    assert parsed.tables["rounds"][0]["bomb_site"] == "A"
    assert parsed.tables["rounds"][0]["t_team"] == "Team A"
    assert parsed.tables["rounds"][0]["ct_team"] == "Team B"
    assert parsed.tables["shots"][0]["weapon"] == "ak47"
    assert parsed.tables["grenades"][0]["grenade_type"] == "flash"
    assert parsed.tables["blinds"][0]["is_enemy"] is True
    assert parsed.tables["replay_frames"] == parsed.tables["ticks"]

    for table, schema in PARQUET_SCHEMAS.items():
        assert set(parsed.tables[table][0]) == set(schema) if parsed.tables[table] else True
        assert all("radar_x" not in row and "radar_y" not in row for row in parsed.tables[table])
