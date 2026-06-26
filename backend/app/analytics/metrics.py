"""Funções puras de métricas analíticas (sem I/O nem dependências pesadas).

Isolar a lógica de cálculo aqui permite testá-la com dados sintéticos sem
PostgreSQL/Parquet/DuckDB. Os módulos `weapons`, `player_stats`, `sites` e
`heatmaps` consomem estas funções; recebem listas de dicts no schema do
contrato de dados (contracts/_shared/data-contract.md).
"""

from __future__ import annotations

import bisect
from collections import defaultdict
from typing import Any


def ratio(num: float, den: float, ndigits: int = 4) -> float:
    return round(num / den, ndigits) if den else 0.0


# --------------------------------------------------------------------------- #
# First-shot accuracy (heurística de 1º disparo de cada rajada)               #
# --------------------------------------------------------------------------- #


def _has_hit_in_window(sorted_ticks: list[int], start: int, window: int) -> bool:
    """Há algum dano em [start, start+window] na lista de ticks ordenada?"""
    idx = bisect.bisect_left(sorted_ticks, start)
    return idx < len(sorted_ticks) and sorted_ticks[idx] <= start + window


def first_shot_stats(
    shots: list[dict[str, Any]],
    damages: list[dict[str, Any]],
    *,
    burst_gap_ticks: int = 64,
    hit_window_ticks: int = 64,
) -> dict[tuple[str, str], dict[str, int]]:
    """Estatística de first-shot por (steam_id, weapon).

    Agrupa os disparos em **rajadas** (nova rajada quando muda de round ou o gap
    para o disparo anterior excede `burst_gap_ticks`) e marca o 1º disparo da
    rajada como acerto se houver `player_hurt` do mesmo atacante/arma no mesmo
    round dentro de `hit_window_ticks` após o disparo. É uma aproximação.

    Retorna `{(steam_id, weapon): {"bursts": int, "first_hits": int}}`.
    """
    dmg_ticks: dict[tuple[str, str, int], list[int]] = defaultdict(list)
    for dmg in damages:
        key = (dmg.get("attacker_steam_id"), dmg.get("weapon"), dmg.get("round_number"))
        tick = dmg.get("tick")
        if key[0] and key[1] and tick is not None:
            dmg_ticks[key].append(int(tick))
    for ticks in dmg_ticks.values():
        ticks.sort()

    shots_by_key: dict[tuple[str, str], list[tuple[int, int]]] = defaultdict(list)
    for shot in shots:
        steam_id = shot.get("steam_id")
        weapon = shot.get("weapon")
        tick = shot.get("tick")
        if not steam_id or not weapon or tick is None:
            continue
        shots_by_key[(steam_id, weapon)].append((int(shot.get("round_number") or 0), int(tick)))

    result: dict[tuple[str, str], dict[str, int]] = {}
    for (steam_id, weapon), rows in shots_by_key.items():
        rows.sort()
        bursts = 0
        first_hits = 0
        prev_round: int | None = None
        prev_tick: int | None = None
        for round_number, tick in rows:
            new_burst = (
                prev_round != round_number
                or prev_tick is None
                or (tick - prev_tick) > burst_gap_ticks
            )
            if new_burst:
                bursts += 1
                ticks = dmg_ticks.get((steam_id, weapon, round_number), [])
                if _has_hit_in_window(ticks, tick, hit_window_ticks):
                    first_hits += 1
            prev_round, prev_tick = round_number, tick
        result[(steam_id, weapon)] = {"bursts": bursts, "first_hits": first_hits}
    return result


# --------------------------------------------------------------------------- #
# Trade kills                                                                  #
# --------------------------------------------------------------------------- #


def count_trade_kills(
    kills: list[dict[str, Any]],
    *,
    window_seconds: float = 5.0,
) -> dict[str, int]:
    """Conta trade kills por atacante.

    Um kill de A→V é trade quando, no mesmo round e até `window_seconds` antes,
    V havia matado um companheiro de A (vítima anterior do mesmo lado de A).
    """
    result: dict[str, int] = defaultdict(int)
    by_round: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for kill in kills:
        by_round[kill.get("round_number")].append(kill)

    for round_kills in by_round.values():
        ordered = sorted(
            round_kills,
            key=lambda r: (float(r.get("time") or 0.0), int(r.get("tick") or 0)),
        )
        for i, kill in enumerate(ordered):
            attacker = kill.get("attacker_steam_id")
            victim = kill.get("victim_steam_id")
            attacker_side = kill.get("attacker_side")
            if not attacker or not victim:
                continue
            t_now = float(kill.get("time") or 0.0)
            for j in range(i):
                prev = ordered[j]
                if prev.get("attacker_steam_id") != victim:
                    continue
                # A vítima atual (V) havia matado um companheiro de A?
                if prev.get("victim_side") != attacker_side:
                    continue
                if 0 <= t_now - float(prev.get("time") or 0.0) <= window_seconds:
                    result[attacker] += 1
                    break
    return dict(result)


# --------------------------------------------------------------------------- #
# Clutches (1vX vencido)                                                       #
# --------------------------------------------------------------------------- #


def count_clutches(
    kills: list[dict[str, Any]],
    rounds: list[dict[str, Any]],
    players: list[dict[str, Any]],
) -> dict[str, int]:
    """Conta clutches vencidos por jogador.

    Um clutch é creditado quando o jogador ficou como **último vivo** do seu time
    diante de ≥1 inimigo vivo (1vX) e o time dele **venceu** o round. O lado de
    cada jogador por round é derivado de `team` × `t_team`/`ct_team`.
    """
    team_by_player = {p.get("steam_id"): p.get("team") for p in players}
    kills_by_round: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for kill in kills:
        kills_by_round[kill.get("round_number")].append(kill)

    result: dict[str, int] = defaultdict(int)
    for round_row in rounds:
        winner = round_row.get("winner")
        if winner not in {"CT", "T"}:
            continue
        t_team = round_row.get("t_team")
        ct_team = round_row.get("ct_team")

        def side_of(
            steam_id: str, t_team: str | None = t_team, ct_team: str | None = ct_team
        ) -> str | None:
            team = team_by_player.get(steam_id)
            if team and team == t_team:
                return "T"
            if team and team == ct_team:
                return "CT"
            return None

        alive: dict[str, set[str]] = {"T": set(), "CT": set()}
        for steam_id in team_by_player:
            side = side_of(steam_id)
            if side:
                alive[side].add(steam_id)

        clutcher: dict[str, str | None] = {"T": None, "CT": None}
        round_kills = sorted(
            kills_by_round.get(round_row.get("round_number"), []),
            key=lambda r: int(r.get("tick") or 0),
        )
        for kill in round_kills:
            victim = kill.get("victim_steam_id")
            side = side_of(victim) if victim else None
            if side is None or victim not in alive[side]:
                continue
            alive[side].discard(victim)
            if len(alive[side]) == 1 and clutcher[side] is None:
                other = "CT" if side == "T" else "T"
                if len(alive[other]) >= 1:
                    clutcher[side] = next(iter(alive[side]))

        last = clutcher.get(winner)
        if last is not None:
            result[last] += 1
    return dict(result)


# --------------------------------------------------------------------------- #
# Sucesso por bombsite                                                         #
# --------------------------------------------------------------------------- #


def compute_bombsites(rounds: list[dict[str, Any]]) -> dict[str, Any]:
    """Win rate por (time, site).

    `win_rate` = rounds vencidos / rounds atribuídos ao site (`bomb_site`).
    `post_plant_win_rate` = vitórias após plant concretizado (`plant_tick`
    presente e sem defuse) / rounds com plant concretizado. As duas divergem
    quando há rounds atribuídos ao site sem plant efetivo.
    """
    grouped: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"plants": 0, "round_wins": 0, "planted": 0, "post_plant_wins": 0}
    )
    for round_row in rounds:
        site = round_row.get("bomb_site")
        team = round_row.get("t_team")
        if not site or not team:
            continue
        item = grouped[(team, site)]
        item["plants"] += 1
        won = round_row.get("winner") == "T"
        if won:
            item["round_wins"] += 1
        if round_row.get("plant_tick") is not None:
            item["planted"] += 1
            if won and round_row.get("defuse_tick") is None:
                item["post_plant_wins"] += 1

    sites: list[dict[str, Any]] = []
    best_by_team: dict[str, str] = {}
    best_rate: dict[str, float] = {}
    for (team, site), item in sorted(grouped.items()):
        plants = item["plants"]
        win_rate = ratio(item["round_wins"], plants)
        post_plant_win_rate = ratio(item["post_plant_wins"], item["planted"])
        sites.append(
            {
                "team": team,
                "site": site,
                "plants": plants,
                "round_wins": item["round_wins"],
                "win_rate": win_rate,
                "post_plant_win_rate": post_plant_win_rate,
            }
        )
        if team not in best_rate or win_rate > best_rate[team]:
            best_rate[team] = win_rate
            best_by_team[team] = site
    return {"sites": sites, "best_site_by_team": best_by_team}


# --------------------------------------------------------------------------- #
# Round range (filtro de heatmap)                                             #
# --------------------------------------------------------------------------- #


def parse_round_range(round_range: str | None) -> tuple[int | None, int | None] | None:
    """Interpreta `"a-b"`, `"a-"`, `"-b"` ou `"a"`; `None`/vazio = sem filtro.

    Levanta `ValueError` para entrada malformada (o endpoint converte em 400).
    """
    if not round_range:
        return None
    text = round_range.strip()
    if not text:
        return None
    if "-" in text:
        lo_text, hi_text = text.split("-", 1)
        lo = int(lo_text) if lo_text.strip() else None
        hi = int(hi_text) if hi_text.strip() else None
    else:
        lo = hi = int(text)
    return (lo, hi)


def in_round_range(round_number: int, parsed: tuple[int | None, int | None] | None) -> bool:
    if parsed is None:
        return True
    lo, hi = parsed
    if lo is not None and round_number < lo:
        return False
    if hi is not None and round_number > hi:
        return False
    return True
