"""Payload de replay 2D offline."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.analytics.map_projection import RadarMetadata, world_to_radar
from app.analytics.reader import read_tables

# Duração (s) do efeito ativo por tipo de granada (fumaça/fogo persistem).
_GRENADE_LIFETIME = {"smoke": 18.0, "molotov": 7.0, "incendiary": 7.0, "decoy": 15.0}


def build_replay(
    match_id: str,
    map_name: str,
    tick_rate: int | None,
    round_number: int,
    sample_rate: int,
    metadata: RadarMetadata,
) -> dict[str, Any]:
    tables = read_tables(match_id, "replay_frames", "kills", "bomb_events", "grenades", "blinds")
    frame_rows = [row for row in tables["replay_frames"] if row["round_number"] == round_number]
    unique_ticks = sorted({row["tick"] for row in frame_rows})
    sample_rate = max(1, sample_rate)
    selected_ticks = set(unique_ticks[::sample_rate])
    rate = tick_rate or 64

    # Posições por jogador (todos os ticks do round) — para a granada em voo.
    frames_by_steam: dict[str, list[tuple[int, float, float]]] = defaultdict(list)
    for row in frame_rows:
        frames_by_steam[row["steam_id"]].append((row["tick"], row["x"], row["y"]))
    for positions in frames_by_steam.values():
        positions.sort()

    # Intervalos de cegueira por vítima (para marcar quem está cego em cada frame).
    blind_intervals: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for row in tables["blinds"]:
        if row["round_number"] != round_number:
            continue
        victim = row.get("victim_steam_id")
        duration = float(row.get("duration") or 0.0)
        if victim and duration > 0:
            blind_intervals[victim].append((row["tick"], row["tick"] + int(duration * rate)))

    def _blinded(steam: str, tick: int) -> bool:
        return any(start <= tick <= end for start, end in blind_intervals.get(steam, []))

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
                "blinded": _blinded(row["steam_id"], row["tick"]),
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
    grenade_objects = _grenade_objects(
        tables["grenades"], round_number, rate, metadata, frames_by_steam
    )
    return {
        "match_id": match_id,
        "map": map_name,
        "round": round_number,
        "tick_rate": tick_rate,
        "frames": frames,
        "grenades": grenade_objects,
    }


def _pos_at(
    frames_by_steam: dict[str, list[tuple[int, float, float]]],
    steam: str | None,
    tick: int,
    metadata: RadarMetadata,
) -> dict[str, float | None] | None:
    rows = frames_by_steam.get(steam or "")
    if not rows:
        return None
    chosen = rows[0]
    for entry in rows:
        if entry[0] <= tick:
            chosen = entry
        else:
            break
    return world_to_radar(chosen[1], chosen[2], metadata)


def _grenade_objects(
    grenades: list[dict],
    round_number: int,
    rate: int,
    metadata: RadarMetadata,
    frames_by_steam: dict[str, list[tuple[int, float, float]]],
) -> list[dict[str, Any]]:
    """Granadas como objetos: voo (arremesso→detonação) + efeito ativo (fumaça/fogo)."""
    round_grenades = [row for row in grenades if row["round_number"] == round_number]
    thrown_by_key: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row in round_grenades:
        if row.get("event") == "thrown" and row.get("thrower_steam_id"):
            thrown_by_key[(row["thrower_steam_id"], row["grenade_type"])].append(row["tick"])
    for ticks in thrown_by_key.values():
        ticks.sort()

    objects: list[dict[str, Any]] = []
    # molotov/incendiária via inferno emitem vários eventos; mantém só 1 por janela.
    last_fire: dict[str, int] = {}
    for row in sorted(round_grenades, key=lambda r: r["tick"]):
        if row.get("event") != "detonate":
            continue
        gtype = row["grenade_type"]
        detonate_tick = row["tick"]
        if gtype in {"molotov", "incendiary"}:
            key = row.get("thrower_steam_id") or "?"
            if key in last_fire and detonate_tick - last_fire[key] <= 3 * rate:
                continue
            last_fire[key] = detonate_tick
        thrower = row.get("thrower_steam_id")
        candidates = thrown_by_key.get((thrower, gtype), []) if thrower else []
        prior = [t for t in candidates if t <= detonate_tick and detonate_tick - t <= 10 * rate]
        thrown_tick = prior[-1] if prior else None
        start = _pos_at(frames_by_steam, thrower, thrown_tick, metadata) if thrown_tick else None
        end = world_to_radar(row.get("x"), row.get("y"), metadata)
        lifetime = _GRENADE_LIFETIME.get(gtype, 0.0)
        objects.append(
            {
                "type": gtype,
                "thrower_steam_id": thrower,
                "thrown_tick": thrown_tick,
                "detonate_tick": detonate_tick,
                "expire_tick": detonate_tick + int(lifetime * rate),
                "start_radar_x": start["radar_x"] if start else None,
                "start_radar_y": start["radar_y"] if start else None,
                "radar_x": end["radar_x"],
                "radar_y": end["radar_y"],
            }
        )
    return objects


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
        if row["round_number"] == round_number and row.get("event") == "detonate":
            events_by_tick[row["tick"]].append(
                {
                    "type": "grenade",
                    "grenade_type": row["grenade_type"],
                    "tick": row["tick"],
                    **_event_position(row, "x", "y", metadata),
                }
            )
