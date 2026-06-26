"""Phase 07: adapter awpy -> schema canônico do cs2-lab.

Usa os **nomes de coluna reais** do awpy (round_num, attacker_steamid,
attacker_X, winner minúsculo, bombsite='BombsiteA'/'not_planted', side='t'/'ct')
para validar o mapeamento de verdade. Granadas/flashes vêm do demoparser2
(híbrido) — aqui o supplement é stubado.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import polars as pl

from app.parsers.parse_with_awpy import parse_demo
from app.parsers.schema import PARQUET_SCHEMAS


class _FakeAwpyDemo:
    def __init__(self, _path: str) -> None:
        # Header real do awpy só traz map_name (sem times/tick_rate).
        self.header = {"map_name": "de_mirage"}

    def parse(
        self,
        events: list[str] | None = None,
        player_props: list[str] | None = None,
        other_props: list[str] | None = None,
    ) -> None:
        # Registra os props pedidos: o adapter precisa solicitar "yaw" ao awpy,
        # senão o ângulo de mira (FOV) sai nulo.
        self.player_props = player_props
        self.rounds = pl.DataFrame(
            [
                {
                    "round_num": 1,
                    "start": 1000,
                    "freeze_end": 1500,
                    "end": 5000,
                    "official_end": 5400,
                    "winner": "t",  # minúsculo no awpy
                    "reason": "bomb",
                    "bomb_plant": 3000,
                    "bomb_site": "BombsiteA",
                }
            ]
        )
        self.kills = pl.DataFrame(
            [
                {
                    "round_num": 1,
                    "tick": 3500,
                    "attacker_steamid": "76561198000000001",
                    "victim_steamid": "76561198000000002",
                    "assister_steamid": None,
                    "weapon": "ak47",
                    "headshot": True,
                    "attacker_side": "t",
                    "victim_side": "ct",
                    "attacker_X": 10.0,
                    "attacker_Y": 20.0,
                    "attacker_Z": 0.0,
                    "victim_X": 30.0,
                    "victim_Y": 40.0,
                    "victim_Z": 0.0,
                }
            ]
        )
        self.damages = pl.DataFrame(
            [
                {
                    "round_num": 1,
                    "tick": 3400,
                    "attacker_steamid": "76561198000000001",
                    "victim_steamid": "76561198000000002",
                    "weapon": "ak47",
                    "dmg_health": 100,
                    "dmg_armor": 12,
                    "hitgroup": "head",
                }
            ]
        )
        self.shots = pl.DataFrame(
            [
                {
                    "round_num": 1,
                    "tick": 3300,
                    "player_steamid": "76561198000000001",
                    "player_side": "t",
                    "weapon": "ak47",
                    "player_X": 10.0,
                    "player_Y": 20.0,
                    "player_Z": 0.0,
                }
            ]
        )
        self.bomb = pl.DataFrame(
            [
                {
                    "round_num": 1,
                    "tick": 3000,
                    "event": "planted",  # _bomb_event -> "plant"
                    "steamid": "76561198000000001",
                    "name": "alpha",
                    "bombsite": "BombsiteA",
                    "X": 50.0,
                    "Y": 60.0,
                    "Z": 0.0,
                }
            ]
        )
        self.ticks = pl.DataFrame(
            [
                {
                    "round_num": 1,
                    "tick": 2400,
                    "steamid": "76561198000000001",
                    "name": "alpha",
                    "side": "t",
                    "place": "A site",
                    "health": 100,
                    "X": 9.0,
                    "Y": 19.0,
                    "Z": 0.0,
                    "yaw": -42.5,
                },
                {
                    "round_num": 1,
                    "tick": 2400,
                    "steamid": "76561198000000002",
                    "name": "bravo",
                    "side": "ct",
                    "place": "A site",
                    "health": 100,
                    "X": 29.0,
                    "Y": 39.0,
                    "Z": 0.0,
                    "yaw": 31.0,
                },
            ]
        )


def _fake_utility(demo_path, *, match_id, tick_rate, side_of, round_start_of):
    # Verifica que o side_of resolve o lado a partir dos ticks do awpy.
    flasher_side = side_of(1, "76561198000000001")
    victim_side = side_of(1, "76561198000000002")
    return {
        "grenades": [
            {
                "match_id": match_id,
                "round_number": 1,
                "tick": 2600,
                "time": 17.1875,
                "thrower_steam_id": "76561198000000001",
                "thrower_side": flasher_side,
                "grenade_type": "flash",
                "event": "thrown",
                "x": None,
                "y": None,
                "z": None,
                "entity_id": None,
            }
        ],
        "blinds": [
            {
                "match_id": match_id,
                "round_number": 1,
                "tick": 2620,
                "time": 17.5,
                "flasher_steam_id": "76561198000000001",
                "victim_steam_id": "76561198000000002",
                "flasher_side": flasher_side,
                "victim_side": victim_side,
                "is_enemy": flasher_side != victim_side,
                "duration": 2.1,
                "entity_id": 7,
            }
        ],
    }


def test_awpy_adapter_maps_real_columns_to_contract_schema(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.parsers.parse_with_demoparser2.extract_utility_events", _fake_utility
    )
    match_id = str(uuid.uuid4())

    parsed = parse_demo(
        Path("fixture.dem"),
        match_id=match_id,
        demo_factory=_FakeAwpyDemo,
    )

    assert parsed.match.map == "de_mirage"
    assert parsed.match.team_a == "Team A"
    assert parsed.match.tick_rate == 64

    # winner minúsculo do awpy normalizado para maiúsculo.
    round_row = parsed.tables["rounds"][0]
    assert round_row["winner"] == "T"
    assert round_row["bomb_planted"] is True
    assert round_row["bomb_site"] == "A"
    assert round_row["plant_tick"] == 3000

    # kills: posições e side a partir das colunas reais.
    kill = parsed.tables["kills"][0]
    assert kill["attacker_steam_id"] == "76561198000000001"
    assert kill["attacker_side"] == "T"
    assert kill["victim_side"] == "CT"
    assert kill["attacker_x"] == 10.0

    assert parsed.tables["damages"][0]["hp_damage"] == 100
    assert parsed.tables["shots"][0]["steam_id"] == "76561198000000001"

    bomb = parsed.tables["bomb_events"][0]
    assert bomb["event"] == "plant"
    assert bomb["site"] == "A"
    assert bomb["steam_id"] == "76561198000000001"

    tick_row = parsed.tables["ticks"][0]
    assert tick_row["side"] in {"T", "CT"}
    assert tick_row["x"] == 9.0
    # yaw (ângulo de mira) mapeado a partir dos ticks do awpy — alimenta o FOV.
    assert tick_row["yaw"] == -42.5

    # granadas/flashes vêm do supplement (demoparser2); side resolvido via ticks.
    assert parsed.tables["grenades"][0]["grenade_type"] == "flash"
    assert parsed.tables["blinds"][0]["is_enemy"] is True
    assert parsed.tables["blinds"][0]["flasher_side"] == "T"

    # replay_frames é downsample de ticks; nenhuma tabela carrega radar_x/radar_y.
    assert parsed.tables["replay_frames"]
    for table in PARQUET_SCHEMAS:
        assert all("radar_x" not in row for row in parsed.tables[table])
        if parsed.tables[table]:
            assert set(parsed.tables[table][0]) == set(PARQUET_SCHEMAS[table])


def test_awpy_parse_requests_yaw_prop(monkeypatch) -> None:
    """O adapter deve pedir explicitamente o prop 'yaw' ao awpy (senão o FOV some)."""
    monkeypatch.setattr(
        "app.parsers.parse_with_demoparser2.extract_utility_events", _fake_utility
    )
    holder: dict[str, _FakeAwpyDemo] = {}

    def factory(path: str) -> _FakeAwpyDemo:
        demo = _FakeAwpyDemo(path)
        holder["demo"] = demo
        return demo

    parse_demo(Path("fixture.dem"), match_id=str(uuid.uuid4()), demo_factory=factory)

    assert holder["demo"].player_props is not None
    assert "yaw" in holder["demo"].player_props
