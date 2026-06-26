"""Testes unitários puros das métricas analíticas (Phase 08).

Não dependem de PostgreSQL/Parquet/DuckDB: exercitam a lógica de
`app.analytics.metrics` com dados sintéticos que cobrem cenários que o mock
fallback não produz (trades, clutches, first-shot, post-plant, round range).
"""

from __future__ import annotations

import pytest

from app.analytics.metrics import (
    compute_bombsites,
    count_clutches,
    count_trade_kills,
    first_shot_stats,
    in_round_range,
    parse_round_range,
)


def test_first_shot_stats_groups_bursts_and_detects_first_hit() -> None:
    shots = [
        {"steam_id": "s1", "weapon": "ak47", "round_number": 1, "tick": 100},
        {"steam_id": "s1", "weapon": "ak47", "round_number": 1, "tick": 110},
        {"steam_id": "s1", "weapon": "ak47", "round_number": 1, "tick": 120},
        # gap > 64 ticks => nova rajada
        {"steam_id": "s1", "weapon": "ak47", "round_number": 1, "tick": 300},
        {"steam_id": "s1", "weapon": "ak47", "round_number": 1, "tick": 310},
    ]
    damages = [
        # 1ª rajada (tick 100): dano só em 200 => fora da janela de 64 => erro
        {"attacker_steam_id": "s1", "weapon": "ak47", "round_number": 1, "tick": 200},
        # 2ª rajada (tick 300): dano em 305 => dentro da janela => acerto
        {"attacker_steam_id": "s1", "weapon": "ak47", "round_number": 1, "tick": 305},
    ]
    stats = first_shot_stats(shots, damages)
    assert stats[("s1", "ak47")] == {"bursts": 2, "first_hits": 1}


def test_first_shot_new_burst_on_round_change() -> None:
    shots = [
        {"steam_id": "s1", "weapon": "awp", "round_number": 1, "tick": 100},
        {"steam_id": "s1", "weapon": "awp", "round_number": 2, "tick": 110},
    ]
    stats = first_shot_stats(shots, [])
    assert stats[("s1", "awp")]["bursts"] == 2
    assert stats[("s1", "awp")]["first_hits"] == 0


def test_count_trade_kills_credits_the_avenger_within_window() -> None:
    kills = [
        # V (CT) mata um companheiro de A (T)
        {"round_number": 1, "tick": 100, "time": 10.0, "attacker_steam_id": "V",
         "victim_steam_id": "mate", "attacker_side": "CT", "victim_side": "T"},
        # A (T) mata V dentro de 5s => trade para A
        {"round_number": 1, "tick": 200, "time": 12.0, "attacker_steam_id": "A",
         "victim_steam_id": "V", "attacker_side": "T", "victim_side": "CT"},
        # B mata W sem morte prévia de companheiro => não é trade
        {"round_number": 1, "tick": 300, "time": 30.0, "attacker_steam_id": "B",
         "victim_steam_id": "W", "attacker_side": "T", "victim_side": "CT"},
    ]
    assert count_trade_kills(kills) == {"A": 1}


def test_count_trade_kills_respects_time_window() -> None:
    kills = [
        {"round_number": 1, "tick": 100, "time": 10.0, "attacker_steam_id": "V",
         "victim_steam_id": "mate", "attacker_side": "CT", "victim_side": "T"},
        # 6s depois => fora da janela de 5s => não é trade
        {"round_number": 1, "tick": 600, "time": 16.0, "attacker_steam_id": "A",
         "victim_steam_id": "V", "attacker_side": "T", "victim_side": "CT"},
    ]
    assert count_trade_kills(kills) == {}


def test_count_clutches_awards_last_alive_winner() -> None:
    players = [
        {"steam_id": "p1", "team": "TeamT"}, {"steam_id": "p2", "team": "TeamT"},
        {"steam_id": "e1", "team": "TeamC"}, {"steam_id": "e2", "team": "TeamC"},
    ]
    rounds = [{"round_number": 1, "winner": "T", "t_team": "TeamT", "ct_team": "TeamC"}]
    kills = [
        # p2 morre => p1 fica 1v2
        {"round_number": 1, "tick": 100, "victim_steam_id": "p2"},
        {"round_number": 1, "tick": 200, "victim_steam_id": "e1"},
        {"round_number": 1, "tick": 300, "victim_steam_id": "e2"},
    ]
    assert count_clutches(kills, rounds, players) == {"p1": 1}


def test_count_clutches_not_awarded_when_team_loses() -> None:
    players = [
        {"steam_id": "p1", "team": "TeamT"}, {"steam_id": "p2", "team": "TeamT"},
        {"steam_id": "e1", "team": "TeamC"}, {"steam_id": "e2", "team": "TeamC"},
    ]
    # p1 ficou 1v2 mas o round foi vencido pelos CT => sem clutch
    rounds = [{"round_number": 1, "winner": "CT", "t_team": "TeamT", "ct_team": "TeamC"}]
    kills = [
        {"round_number": 1, "tick": 100, "victim_steam_id": "p2"},
        {"round_number": 1, "tick": 200, "victim_steam_id": "p1"},
    ]
    assert count_clutches(kills, rounds, players) == {}


def test_compute_bombsites_separates_win_rate_from_post_plant() -> None:
    rounds = [
        # site A: win com plant concretizado sem defuse
        {"round_number": 1, "t_team": "TeamA", "bomb_site": "A", "winner": "T",
         "plant_tick": 100, "defuse_tick": None},
        # site A: plant concretizado mas defusado => derrota
        {"round_number": 2, "t_team": "TeamA", "bomb_site": "A", "winner": "CT",
         "plant_tick": 200, "defuse_tick": 300},
        # site A: vitória atribuída ao site SEM plant efetivo (execução sem plant)
        {"round_number": 3, "t_team": "TeamA", "bomb_site": "A", "winner": "T",
         "plant_tick": None, "defuse_tick": None},
    ]
    result = compute_bombsites(rounds)
    site_a = result["sites"][0]
    assert site_a["team"] == "TeamA"
    assert site_a["site"] == "A"
    assert site_a["plants"] == 3
    assert site_a["round_wins"] == 2
    assert site_a["win_rate"] == round(2 / 3, 4)
    # planted=2 (r1,r2), post_plant_wins=1 (r1) => 0.5, diferente do win_rate
    assert site_a["post_plant_win_rate"] == 0.5
    assert result["best_site_by_team"]["TeamA"] == "A"


def test_parse_and_apply_round_range() -> None:
    assert parse_round_range(None) is None
    assert parse_round_range("") is None
    assert parse_round_range("3") == (3, 3)
    assert parse_round_range("2-4") == (2, 4)
    assert parse_round_range("2-") == (2, None)
    assert parse_round_range("-3") == (None, 3)

    rng = parse_round_range("2-4")
    assert [n for n in range(1, 6) if in_round_range(n, rng)] == [2, 3, 4]
    assert in_round_range(99, None) is True


def test_parse_round_range_rejects_garbage() -> None:
    with pytest.raises(ValueError):
        parse_round_range("abc")
