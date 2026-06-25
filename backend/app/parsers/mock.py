"""Mock parser fallback (Phase 06).

Gera uma partida sintética **no schema exato do contrato de dados** (PostgreSQL +
Parquet, incluindo `grenades`, `blinds` e `shots`), de forma determinística por
`match_id`, para que o fluxo de parsing/analytics funcione sem o parser real.
O mock deve ser indistinguível do real para o frontend.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.parsers.schema import PARQUET_SCHEMAS, to_frame

TICK_RATE = 64
MAP = "de_mirage"
TEAM_A = "Team A"
TEAM_B = "Team B"
N_ROUNDS = 6
WEAPONS = ["ak47", "m4a1", "awp", "deagle", "glock", "usp_silencer"]
GRENADES = ["he", "flash", "smoke", "molotov"]


@dataclass
class PlayerMeta:
    steam_id: str
    name: str
    team: str
    starting_side: str


@dataclass
class RoundMeta:
    round_number: int
    winner: str
    reason: str
    start_tick: int
    end_tick: int


@dataclass
class MatchMeta:
    map: str
    team_a: str
    team_b: str
    score_a: int
    score_b: int
    tick_rate: int
    started_at: datetime
    players: list[PlayerMeta]
    rounds: list[RoundMeta]


def _players() -> list[PlayerMeta]:
    players: list[PlayerMeta] = []
    for i in range(10):
        team = TEAM_A if i < 5 else TEAM_B
        side = "T" if team == TEAM_A else "CT"
        players.append(
            PlayerMeta(
                steam_id=f"76561198000000{i:03d}",
                name=f"player_{i:02d}",
                team=team,
                starting_side=side,
            )
        )
    return players


def generate_and_write(match_id: str, demo_path: str, parquet_dir: Path) -> MatchMeta:
    """Gera os dados sintéticos e grava os Parquet em `parquet_dir/match_id=<id>/`."""
    players = _players()
    t_players = [p for p in players if p.team == TEAM_A]
    ct_players = [p for p in players if p.team == TEAM_B]

    rounds_meta: list[RoundMeta] = []
    rows: dict[str, list[dict]] = {name: [] for name in PARQUET_SCHEMAS}

    score_a = score_b = 0
    entity = 1000
    for rn in range(1, N_ROUNDS + 1):
        start = rn * 100_000
        end = start + 60 * TICK_RATE
        # Mock sem troca de lado: Team A sempre T, Team B sempre CT.
        winner = "T" if rn % 2 == 1 else "CT"
        if winner == "T":
            score_a += 1
        else:
            score_b += 1

        bomb_planted = rn == 3
        bomb_site = "A" if bomb_planted else None
        plant_tick = start + 3000 if bomb_planted else None
        reason = "bomb" if (bomb_planted and winner == "T") else "elimination"
        rounds_meta.append(RoundMeta(rn, winner, reason, start, end))

        rows["rounds"].append(
            {
                "match_id": match_id, "round_number": rn, "winner": winner,
                "reason": reason, "start_tick": start, "end_tick": end,
                "bomb_planted": bomb_planted, "bomb_site": bomb_site,
                "plant_tick": plant_tick, "defuse_tick": None,
                "t_team": TEAM_A, "ct_team": TEAM_B,
            }
        )

        if bomb_planted:
            planter = t_players[0]
            rows["bomb_events"].append(
                {
                    "match_id": match_id, "round_number": rn, "tick": plant_tick,
                    "time": (plant_tick - start) / TICK_RATE, "event": "plant",
                    "steam_id": planter.steam_id, "site": "A",
                    "x": -1500.0, "y": -200.0, "z": -100.0,
                }
            )
            if winner == "T":
                rows["bomb_events"].append(
                    {
                        "match_id": match_id, "round_number": rn,
                        "tick": plant_tick + 4000,
                        "time": (plant_tick + 4000 - start) / TICK_RATE,
                        "event": "explode", "steam_id": None, "site": "A",
                        "x": -1500.0, "y": -200.0, "z": -100.0,
                    }
                )

        winners = t_players if winner == "T" else ct_players
        losers = ct_players if winner == "T" else t_players
        wside = winner
        lside = "CT" if winner == "T" else "T"

        for k in range(5):
            atk = winners[k % len(winners)]
            vic = losers[k % len(losers)]
            tick = start + 1000 + k * 500
            weapon = WEAPONS[k % len(WEAPONS)]
            hs = k % 2 == 0
            rows["kills"].append(
                {
                    "match_id": match_id, "round_number": rn, "tick": tick,
                    "time": (tick - start) / TICK_RATE,
                    "attacker_steam_id": atk.steam_id,
                    "victim_steam_id": vic.steam_id, "assister_steam_id": None,
                    "weapon": weapon, "headshot": hs, "attacker_side": wside,
                    "victim_side": lside, "attacker_x": -2000.0 + k * 100,
                    "attacker_y": 500.0 + k * 50, "attacker_z": -100.0,
                    "victim_x": -1800.0 + k * 100, "victim_y": 400.0 + k * 50,
                    "victim_z": -100.0,
                }
            )
            rows["damages"].append(
                {
                    "match_id": match_id, "round_number": rn, "tick": tick - 100,
                    "time": (tick - 100 - start) / TICK_RATE,
                    "attacker_steam_id": atk.steam_id,
                    "victim_steam_id": vic.steam_id, "weapon": weapon,
                    "hp_damage": 100 if hs else 60, "armor_damage": 10,
                    "hitgroup": "head" if hs else "chest",
                }
            )
            for s in range(4):
                stick = tick - 200 + s * 20
                rows["shots"].append(
                    {
                        "match_id": match_id, "round_number": rn, "tick": stick,
                        "time": (stick - start) / TICK_RATE,
                        "steam_id": atk.steam_id, "weapon": weapon,
                        "x": -2000.0 + k * 100, "y": 500.0 + k * 50, "z": -100.0,
                    }
                )

        for gi, gtype in enumerate(GRENADES):
            thr = winners[gi % len(winners)]
            gtick = start + 500 + gi * 300
            entity += 1
            rows["grenades"].append(
                {
                    "match_id": match_id, "round_number": rn, "tick": gtick,
                    "time": (gtick - start) / TICK_RATE,
                    "thrower_steam_id": thr.steam_id, "thrower_side": wside,
                    "grenade_type": gtype, "event": "thrown",
                    "x": -1900.0 + gi * 50, "y": 300.0 + gi * 40, "z": -100.0,
                    "entity_id": entity,
                }
            )
            rows["grenades"].append(
                {
                    "match_id": match_id, "round_number": rn, "tick": gtick + 200,
                    "time": (gtick + 200 - start) / TICK_RATE,
                    "thrower_steam_id": thr.steam_id, "thrower_side": wside,
                    "grenade_type": gtype, "event": "detonate",
                    "x": -1850.0 + gi * 50, "y": 320.0 + gi * 40, "z": -100.0,
                    "entity_id": entity,
                }
            )
            if gtype == "he":
                vic = losers[gi % len(losers)]
                rows["damages"].append(
                    {
                        "match_id": match_id, "round_number": rn,
                        "tick": gtick + 210, "time": (gtick + 210 - start) / TICK_RATE,
                        "attacker_steam_id": thr.steam_id,
                        "victim_steam_id": vic.steam_id, "weapon": "hegrenade",
                        "hp_damage": 31, "armor_damage": 5, "hitgroup": "generic",
                    }
                )
            if gtype == "molotov":
                vic = losers[gi % len(losers)]
                rows["damages"].append(
                    {
                        "match_id": match_id, "round_number": rn,
                        "tick": gtick + 210, "time": (gtick + 210 - start) / TICK_RATE,
                        "attacker_steam_id": thr.steam_id,
                        "victim_steam_id": vic.steam_id, "weapon": "inferno",
                        "hp_damage": 22, "armor_damage": 0, "hitgroup": "generic",
                    }
                )
            if gtype == "flash":
                vic = losers[gi % len(losers)]
                rows["blinds"].append(
                    {
                        "match_id": match_id, "round_number": rn,
                        "tick": gtick + 210, "time": (gtick + 210 - start) / TICK_RATE,
                        "flasher_steam_id": thr.steam_id,
                        "victim_steam_id": vic.steam_id, "flasher_side": wside,
                        "victim_side": lside, "is_enemy": True, "duration": 2.5,
                        "entity_id": entity,
                    }
                )

        for ti in range(3):
            tick = start + ti * 1500
            for p in players:
                rows["ticks"].append(
                    {
                        "match_id": match_id, "round_number": rn, "tick": tick,
                        "time": (tick - start) / TICK_RATE, "steam_id": p.steam_id,
                        "name": p.name, "side": p.starting_side,
                        "x": -2000.0 + ti * 100, "y": 500.0 + ti * 80, "z": -100.0,
                        "yaw": float((ti * 90) % 360), "hp": 100, "armor": 100,
                        "weapon": WEAPONS[ti % len(WEAPONS)], "alive": True,
                    }
                )

        for p in players:
            rows["economy"].append(
                {
                    "match_id": match_id, "round_number": rn, "steam_id": p.steam_id,
                    "side": p.starting_side, "money_start": 4000,
                    "equip_value": 4200, "buy_type": "full",
                }
            )

    # replay_frames = downsample de ticks (aqui, mesma amostragem do mock).
    rows["replay_frames"] = list(rows["ticks"])

    players_rows = [
        {
            "match_id": match_id, "steam_id": p.steam_id, "name": p.name,
            "team": p.team, "starting_side": p.starting_side,
        }
        for p in players
    ]
    rows["players"] = players_rows

    match_dir = parquet_dir / f"match_id={match_id}"
    match_dir.mkdir(parents=True, exist_ok=True)
    for table in PARQUET_SCHEMAS:
        to_frame(table, rows[table]).write_parquet(match_dir / f"{table}.parquet")

    return MatchMeta(
        map=MAP, team_a=TEAM_A, team_b=TEAM_B, score_a=score_a, score_b=score_b,
        tick_rate=TICK_RATE, started_at=datetime.now(UTC),
        players=players, rounds=rounds_meta,
    )
