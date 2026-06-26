"""Phase 08: API de analytics sobre dados processados."""

from __future__ import annotations

import base64
import json
import uuid

import pytest

from app.core import paths
from app.parsers import mock
from app.storage.duckdb import refresh_views
from app.storage.models import Demo, Match, Player, Round

_PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


@pytest.fixture()
def processed_match(session_factory, tmp_data) -> dict[str, str]:
    match_id = str(uuid.uuid4())
    demo_id = uuid.uuid4()
    meta = mock.generate_and_write(match_id, "fixture.dem", paths.PARQUET_DIR)
    connection = refresh_views(paths.PARQUET_DIR, paths.DUCKDB_PATH)
    connection.close()

    paths.MAPS_RADAR_INFO_DIR.mkdir(parents=True, exist_ok=True)
    paths.MAPS_RADARS_DIR.mkdir(parents=True, exist_ok=True)
    (paths.MAPS_RADAR_INFO_DIR / "de_mirage.json").write_text(
        json.dumps(
            {
                "map": "de_mirage",
                "pos_x": -3230,
                "pos_y": 1713,
                "scale": 5.0,
                "image_width": 1024,
                "image_height": 1024,
                "levels": None,
            }
        ),
        encoding="utf-8",
    )
    (paths.MAPS_RADARS_DIR / "de_mirage.png").write_bytes(_PNG_1X1)

    session = session_factory()
    demo = Demo(
        id=demo_id,
        filename="fixture.dem",
        path="fixture.dem",
        status="parsed",
    )
    session.add(demo)
    match_uuid = uuid.UUID(match_id)
    session.add(
        Match(
            id=match_uuid,
            demo_id=demo_id,
            map=meta.map,
            team_a=meta.team_a,
            team_b=meta.team_b,
            score_a=meta.score_a,
            score_b=meta.score_b,
            started_at=meta.started_at,
            tick_rate=meta.tick_rate,
        )
    )
    for player in meta.players:
        session.add(
            Player(
                match_id=match_uuid,
                steam_id=player.steam_id,
                name=player.name,
                team=player.team,
            )
        )
    for round_meta in meta.rounds:
        session.add(
            Round(
                match_id=match_uuid,
                round_number=round_meta.round_number,
                winner=round_meta.winner,
                reason=round_meta.reason,
                start_tick=round_meta.start_tick,
                end_tick=round_meta.end_tick,
            )
        )
    session.commit()
    session.close()
    return {
        "match_id": match_id,
        "team_a_player": meta.players[0].steam_id,
        "team_b_player": meta.players[-1].steam_id,
    }


def test_matches_and_maps_endpoints(client, processed_match) -> None:
    match_id = processed_match["match_id"]

    matches = client.get("/matches")
    assert matches.status_code == 200
    assert matches.json()[0]["id"] == match_id

    detail = client.get(f"/matches/{match_id}")
    assert detail.status_code == 200
    assert detail.json()["map"] == "de_mirage"

    summary = client.get(f"/matches/{match_id}/summary")
    assert summary.status_code == 200
    assert summary.json()["score"] == {"team_a": 3, "team_b": 3}

    rounds = client.get(f"/matches/{match_id}/rounds")
    assert rounds.status_code == 200
    assert len(rounds.json()) == 6

    players = client.get(f"/matches/{match_id}/players")
    assert players.status_code == 200
    assert len(players.json()) == 10

    maps = client.get("/maps")
    assert maps.status_code == 200
    assert "de_mirage" in [item["map"] for item in maps.json()]

    metadata = client.get("/maps/de_mirage/metadata")
    assert metadata.status_code == 200
    assert metadata.json()["scale"] == 5.0

    radar = client.get("/maps/de_mirage/radar")
    assert radar.status_code == 200
    assert radar.headers["content-type"] == "image/png"


def test_stats_endpoints_return_contract_shapes(client, processed_match) -> None:
    match_id = processed_match["match_id"]
    player_id = processed_match["team_b_player"]

    player_stats = client.get(f"/matches/{match_id}/stats/player")
    assert player_stats.status_code == 200
    first = player_stats.json()["players"][0]
    assert {"steam_id", "kills", "deaths", "adr", "kast_pct"} <= set(first)
    # trade_kills/clutches são métricas reais (inteiros), não mais stubs fixos.
    assert isinstance(first["trade_kills"], int)
    assert isinstance(first["clutches"], int)

    utility = client.get(f"/matches/{match_id}/stats/utility")
    assert utility.status_code == 200
    utility_player = utility.json()["players"][0]
    assert utility_player["grenades_thrown"]["total"] > 0
    # grenades_thrown segue exatamente as chaves do contrato (incendiary agrupado em molotov).
    assert set(utility_player["grenades_thrown"]) == {
        "he", "flash", "smoke", "molotov", "decoy", "total",
    }
    assert "enemy_blind_time" in utility_player

    matchups = client.get(f"/matches/{match_id}/stats/matchups")
    assert matchups.status_code == 200
    assert matchups.json()["matrix"][0]["kills"] > 0

    deaths = client.get(f"/matches/{match_id}/stats/death-positions?player={player_id}")
    assert deaths.status_code == 200
    payload = deaths.json()
    assert payload["steam_id"] == player_id
    assert payload["deaths"][0]["radar_x"] is not None
    assert payload["top_spot"]["count"] > 0

    bombsites = client.get(f"/matches/{match_id}/stats/bombsites")
    assert bombsites.status_code == 200
    site = bombsites.json()["sites"][0]
    assert site["site"] == "A"
    assert {"win_rate", "post_plant_win_rate"} <= set(site)


def test_weapons_economy_replay_and_heatmaps(client, processed_match) -> None:
    match_id = processed_match["match_id"]
    player_id = processed_match["team_a_player"]

    weapons = client.get(f"/matches/{match_id}/stats/weapons")
    assert weapons.status_code == 200
    weapon_player = weapons.json()["players"][0]
    assert weapon_player["overall"]["damage_per_shot"] >= 0
    assert "first_shot_accuracy" in weapon_player["overall"]
    assert weapon_player["weapons"][0]["shots"] > 0
    assert "first_shot_accuracy" in weapon_player["weapons"][0]

    economy = client.get(f"/matches/{match_id}/stats/economy")
    assert economy.status_code == 200
    assert economy.json()["rounds"][0]["t_buy"] == "full"
    assert economy.json()["by_player"][0]["avg_equip_value"] == 4200

    replay = client.get(f"/matches/{match_id}/replay?round=1&sample_rate=1")
    assert replay.status_code == 200
    frame = replay.json()["frames"][0]
    assert frame["players"][0]["radar_x"] is not None
    assert isinstance(frame["events"], list)

    for heatmap_type in ("kills", "deaths", "path", "utility", "grenades"):
        query = f"?type={heatmap_type}"
        if heatmap_type == "path":
            query += f"&player={player_id}"
        heatmap = client.get(f"/matches/{match_id}/heatmap{query}")
        assert heatmap.status_code == 200
        payload = heatmap.json()
        assert payload["type"] == heatmap_type
        assert payload["points"]
        assert "radar_x" in payload["points"][0]

    # round_range realmente filtra (não é só ecoado em filters_applied).
    full = client.get(f"/matches/{match_id}/heatmap?type=kills")
    one_round = client.get(f"/matches/{match_id}/heatmap?type=kills&round_range=1-1")
    assert one_round.status_code == 200
    assert one_round.json()["filters_applied"]["round_range"] == "1-1"
    assert 0 < len(one_round.json()["points"]) < len(full.json()["points"])
