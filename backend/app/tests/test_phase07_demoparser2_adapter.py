"""Phase 07: adapter demoparser2 -> schema canônico do cs2-lab."""

from __future__ import annotations

import uuid
from pathlib import Path

import polars as pl

from app.parsers.parse_with_demoparser2 import parse_demo


class _FakeDemoParser:
    def __init__(self, _path: str) -> None:
        self.header = {"map_name": "de_mirage", "tick_rate": 64}

    def parse_event(self, event_name: str, *_args, **_kwargs):
        frames = {
            "player_death": pl.DataFrame(
                [
                    {
                        "round_number": 1,
                        "tick": 3500,
                        "time": 39.0625,
                        "attacker_steam_id": "76561198000000001",
                        "victim_steam_id": "76561198000000002",
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
            ),
            "player_hurt": pl.DataFrame(
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
            ),
            "weapon_fire": pl.DataFrame(
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
            ),
            "bomb_planted": pl.DataFrame(
                [
                    {
                        "round_number": 1,
                        "tick": 3000,
                        "time": 31.25,
                        "steam_id": "76561198000000001",
                        "site": "A",
                        "x": 50.0,
                        "y": 60.0,
                        "z": 0.0,
                    }
                ]
            ),
            "flashbang_detonate": pl.DataFrame(
                [
                    {
                        "round_number": 1,
                        "tick": 2600,
                        "time": 25.0,
                        "thrower_steam_id": "76561198000000001",
                        "thrower_side": "T",
                        "x": 12.0,
                        "y": 22.0,
                        "z": 0.0,
                        "entity_id": 7,
                    }
                ]
            ),
            "player_blind": pl.DataFrame(
                [
                    {
                        "round_number": 1,
                        "tick": 2620,
                        "time": 25.3125,
                        "flasher_steam_id": "76561198000000001",
                        "victim_steam_id": "76561198000000002",
                        "flasher_side": "T",
                        "victim_side": "CT",
                        "duration": 2.1,
                        "entity_id": 7,
                    }
                ]
            ),
        }
        return frames.get(event_name, pl.DataFrame())

    def parse_ticks(self, *_args, **_kwargs):
        return pl.DataFrame(
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


def test_demoparser2_adapter_maps_events_ticks_and_utility() -> None:
    match_id = str(uuid.uuid4())

    parsed = parse_demo(
        Path("fixture.dem"),
        match_id=match_id,
        parser_factory=_FakeDemoParser,
    )

    assert parsed.match.map == "de_mirage"
    assert parsed.tables["kills"][0]["weapon"] == "ak47"
    assert parsed.tables["damages"][0]["hp_damage"] == 100
    assert parsed.tables["shots"][0]["steam_id"] == "76561198000000001"
    assert parsed.tables["bomb_events"][0]["event"] == "plant"
    assert parsed.tables["grenades"][0]["grenade_type"] == "flash"
    assert parsed.tables["blinds"][0]["is_enemy"] is True
    assert parsed.tables["players"][0]["steam_id"] == "76561198000000001"
