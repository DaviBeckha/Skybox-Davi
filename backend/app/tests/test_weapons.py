"""Acurácia por arma: famílias com nome divergente entre eventos.

Bug real: a M4A1-S dispara como `m4a1_silencer` (weapon_fire) mas o dano
(player_hurt) é gravado como `m4a1`; a USP-S dispara como `usp_silencer` e o
dano vira `hkp2000`. Sem canonicalizar, o cruzamento disparo×acerto zera e a
arma aparece com muitos disparos e 0 acertos. Usa apenas `tmp_data`.
"""

from __future__ import annotations

import uuid

from app.analytics.metrics import normalize_weapon
from app.analytics.reader import match_dir
from app.analytics.weapons import build_weapons
from app.parsers.schema import to_frame


def _write(match_id: str, table: str, rows: list[dict]) -> None:
    directory = match_dir(match_id)
    directory.mkdir(parents=True, exist_ok=True)
    to_frame(table, rows).write_parquet(directory / f"{table}.parquet")


def _shot(match_id: str, steam_id: str, weapon: str, tick: int) -> dict:
    return {
        "match_id": match_id,
        "round_number": 1,
        "tick": tick,
        "time": float(tick),
        "steam_id": steam_id,
        "weapon": weapon,
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
    }


def _damage(match_id: str, attacker: str, weapon: str, tick: int, hp: int) -> dict:
    return {
        "match_id": match_id,
        "round_number": 1,
        "tick": tick,
        "time": float(tick),
        "attacker_steam_id": attacker,
        "victim_steam_id": "V",
        "weapon": weapon,
        "hp_damage": hp,
        "armor_damage": 0,
        "hitgroup": "chest",
    }


def test_normalize_weapon_unifies_silenced_families() -> None:
    assert normalize_weapon("weapon_m4a1_silencer") == normalize_weapon("m4a1") == "m4a1"
    assert normalize_weapon("usp_silencer") == normalize_weapon("hkp2000") == "usp"


def test_build_weapons_matches_silenced_shots_to_hits(tmp_data) -> None:
    match_id = str(uuid.uuid4())
    player = {
        "match_id": match_id,
        "steam_id": "A",
        "name": "Ana",
        "team": "T1",
        "starting_side": "CT",
    }
    _write(match_id, "players", [player])
    # M4A1-S: 3 disparos como m4a1_silencer; o dano chega como m4a1.
    # USP-S: 2 disparos como usp_silencer; o dano chega como hkp2000.
    _write(
        match_id,
        "shots",
        [
            _shot(match_id, "A", "m4a1_silencer", 100),
            _shot(match_id, "A", "m4a1_silencer", 110),
            _shot(match_id, "A", "m4a1_silencer", 120),
            _shot(match_id, "A", "usp_silencer", 300),
            _shot(match_id, "A", "usp_silencer", 310),
        ],
    )
    _write(
        match_id,
        "damages",
        [
            _damage(match_id, "A", "m4a1", 102, 30),
            _damage(match_id, "A", "m4a1", 112, 26),
            _damage(match_id, "A", "hkp2000", 302, 20),
        ],
    )
    _write(match_id, "kills", [])

    result = build_weapons(match_id)
    weapons = {w["weapon"]: w for w in result["players"][0]["weapons"]}

    # Famílias unificadas: nada de linha "m4a1_silencer"/"usp_silencer" órfã.
    assert "m4a1_silencer" not in weapons
    assert "usp_silencer" not in weapons

    m4 = weapons["m4a1"]
    assert m4["shots"] == 3
    assert m4["hits"] == 2  # antes do fix: 0
    assert m4["accuracy"] > 0

    usp = weapons["usp"]
    assert usp["shots"] == 2
    assert usp["hits"] == 1  # antes do fix: 0
