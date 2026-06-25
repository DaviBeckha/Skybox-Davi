"""Schemas canônicos das tabelas Parquet (fonte única para mock e parser real).

Os dtypes seguem o contrato de dados (contracts/_shared/data-contract.md, seção 2).
Definir o schema explicitamente garante **paridade** entre o mock (Phase 06) e o
parser real (Phase 07), independentemente de colunas que possam ficar todas nulas.
"""

from __future__ import annotations

import polars as pl

# Ordem e dtypes normativos por tabela.
PARQUET_SCHEMAS: dict[str, dict[str, pl.DataType]] = {
    "rounds": {
        "match_id": pl.Utf8,
        "round_number": pl.Int32,
        "winner": pl.Utf8,
        "reason": pl.Utf8,
        "start_tick": pl.Int64,
        "end_tick": pl.Int64,
        "bomb_planted": pl.Boolean,
        "bomb_site": pl.Utf8,
        "plant_tick": pl.Int64,
        "defuse_tick": pl.Int64,
        "t_team": pl.Utf8,
        "ct_team": pl.Utf8,
    },
    "players": {
        "match_id": pl.Utf8,
        "steam_id": pl.Utf8,
        "name": pl.Utf8,
        "team": pl.Utf8,
        "starting_side": pl.Utf8,
    },
    "economy": {
        "match_id": pl.Utf8,
        "round_number": pl.Int32,
        "steam_id": pl.Utf8,
        "side": pl.Utf8,
        "money_start": pl.Int32,
        "equip_value": pl.Int32,
        "buy_type": pl.Utf8,
    },
    "kills": {
        "match_id": pl.Utf8,
        "round_number": pl.Int32,
        "tick": pl.Int64,
        "time": pl.Float64,
        "attacker_steam_id": pl.Utf8,
        "victim_steam_id": pl.Utf8,
        "assister_steam_id": pl.Utf8,
        "weapon": pl.Utf8,
        "headshot": pl.Boolean,
        "attacker_side": pl.Utf8,
        "victim_side": pl.Utf8,
        "attacker_x": pl.Float64,
        "attacker_y": pl.Float64,
        "attacker_z": pl.Float64,
        "victim_x": pl.Float64,
        "victim_y": pl.Float64,
        "victim_z": pl.Float64,
    },
    "damages": {
        "match_id": pl.Utf8,
        "round_number": pl.Int32,
        "tick": pl.Int64,
        "time": pl.Float64,
        "attacker_steam_id": pl.Utf8,
        "victim_steam_id": pl.Utf8,
        "weapon": pl.Utf8,
        "hp_damage": pl.Int32,
        "armor_damage": pl.Int32,
        "hitgroup": pl.Utf8,
    },
    "shots": {
        "match_id": pl.Utf8,
        "round_number": pl.Int32,
        "tick": pl.Int64,
        "time": pl.Float64,
        "steam_id": pl.Utf8,
        "weapon": pl.Utf8,
        "x": pl.Float64,
        "y": pl.Float64,
        "z": pl.Float64,
    },
    "bomb_events": {
        "match_id": pl.Utf8,
        "round_number": pl.Int32,
        "tick": pl.Int64,
        "time": pl.Float64,
        "event": pl.Utf8,
        "steam_id": pl.Utf8,
        "site": pl.Utf8,
        "x": pl.Float64,
        "y": pl.Float64,
        "z": pl.Float64,
    },
    "grenades": {
        "match_id": pl.Utf8,
        "round_number": pl.Int32,
        "tick": pl.Int64,
        "time": pl.Float64,
        "thrower_steam_id": pl.Utf8,
        "thrower_side": pl.Utf8,
        "grenade_type": pl.Utf8,
        "event": pl.Utf8,
        "x": pl.Float64,
        "y": pl.Float64,
        "z": pl.Float64,
        "entity_id": pl.Int32,
    },
    "blinds": {
        "match_id": pl.Utf8,
        "round_number": pl.Int32,
        "tick": pl.Int64,
        "time": pl.Float64,
        "flasher_steam_id": pl.Utf8,
        "victim_steam_id": pl.Utf8,
        "flasher_side": pl.Utf8,
        "victim_side": pl.Utf8,
        "is_enemy": pl.Boolean,
        "duration": pl.Float64,
        "entity_id": pl.Int32,
    },
    "ticks": {
        "match_id": pl.Utf8,
        "round_number": pl.Int32,
        "tick": pl.Int64,
        "time": pl.Float64,
        "steam_id": pl.Utf8,
        "name": pl.Utf8,
        "side": pl.Utf8,
        "x": pl.Float64,
        "y": pl.Float64,
        "z": pl.Float64,
        "yaw": pl.Float64,
        "hp": pl.Int32,
        "armor": pl.Int32,
        "weapon": pl.Utf8,
        "alive": pl.Boolean,
    },
}
# replay_frames usa o mesmo schema de ticks.
PARQUET_SCHEMAS["replay_frames"] = PARQUET_SCHEMAS["ticks"]


def to_frame(table: str, rows: list[dict]) -> pl.DataFrame:
    """Cria um DataFrame com o schema canônico da tabela (mesmo se `rows` vazio)."""
    schema = PARQUET_SCHEMAS[table]
    return pl.DataFrame(rows, schema=schema, orient="row")
