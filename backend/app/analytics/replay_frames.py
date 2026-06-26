"""Payload de replay 2D offline."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.analytics.map_projection import RadarMetadata, world_to_radar
from app.analytics.reader import read_tables


def build_replay(
    match_id: str,
    map_name: str,
    tick_rate: int | None,
    round_number: int,
    sample_rate: int,
    metadata: RadarMetadata,
) -> dict[str, Any]:
    tables = read_tables(match_id, "replay_frames", "kills", "bomb_events", "grenades")
    frame_rows = [row for row in tables["replay_frames"] if row["round_number"] == round_number]
    unique_ticks = sorted({row["tick"] for row in frame_rows})
    sample_rate = max(1, sample_rate)
    selected_ticks = set(unique_ticks[::sample_rate])
    players_by_tick: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in frame_rows:
        if row["tick"] not in selected_ticks:
            continue
        players_by_tick[row["tick"]].append(
            {
                "steam_id": row["steam_id"],
                "name": row["name"],
                "side": row["side"],
                "x": row["x"],
                "y": row["y"],
                "z": row["z"],
                **world_to_radar(row["x"], row["y"], metadata),
                "hp": row["hp"],
                "armor": row["armor"],
                "weapon": row["weapon"],
                "yaw": row["yaw"],
                "alive": row["alive"],
            }
        )

    events_by_tick: dict[int, list[dict[str, Any]]] = defaultdict(list)
    _add_kill_events(events_by_tick, tables["kills"], round_number, metadata)
    _add_bomb_events(events_by_tick, tables["bomb_events"], round_number, metadata)
    _add_grenade_events(events_by_tick, tables["grenades"], round_number, metadata)

    frames = [
        {
            "tick": tick,
            "time": next((row["time"] for row in frame_rows if row["tick"] == tick), 0.0),
            "players": players_by_tick[tick],
            "events": events_by_tick.get(tick, []),
        }
        for tick in sorted(selected_ticks)
    ]
    return {
        "match_id": match_id,
        "map": map_name,
        "round": round_number,
        "tick_rate": tick_rate,
        "frames": frames,
    }


def _event_position(
    row: dict[str, Any], x_key: str, y_key: str, metadata: RadarMetadata
) -> dict[str, Any]:
    x = row.get(x_key)
    y = row.get(y_key)
    return {"x": x, "y": y, **world_to_radar(x, y, metadata)}


def _add_kill_events(
    events_by_tick: dict[int, list[dict[str, Any]]],
    kills: list[dict],
    round_number: int,
    metadata: RadarMetadata,
) -> None:
    for row in kills:
        if row["round_number"] == round_number:
            events_by_tick[row["tick"]].append(
                {
                    "type": "kill",
                    "grenade_type": None,
                    "tick": row["tick"],
                    **_event_position(row, "victim_x", "victim_y", metadata),
                }
            )


def _add_bomb_events(
    events_by_tick: dict[int, list[dict[str, Any]]],
    bomb_events: list[dict],
    round_number: int,
    metadata: RadarMetadata,
) -> None:
    names = {"plant": "bomb_plant", "defuse": "bomb_defuse", "explode": "bomb_explode"}
    for row in bomb_events:
        if row["round_number"] == round_number:
            events_by_tick[row["tick"]].append(
                {
                    "type": names.get(row["event"], row["event"]),
                    "grenade_type": None,
                    "tick": row["tick"],
                    **_event_position(row, "x", "y", metadata),
                }
            )


def _add_grenade_events(
    events_by_tick: dict[int, list[dict[str, Any]]],
    grenades: list[dict],
    round_number: int,
    metadata: RadarMetadata,
) -> None:
    for row in grenades:
        if row["round_number"] == round_number:
            events_by_tick[row["tick"]].append(
                {
                    "type": "grenade",
                    "grenade_type": row["grenade_type"],
                    "tick": row["tick"],
                    **_event_position(row, "x", "y", metadata),
                }
            )
