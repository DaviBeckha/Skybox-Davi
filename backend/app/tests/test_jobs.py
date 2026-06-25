"""Testes do job de parsing (Phase 06): mock fallback, falha e enfileiramento."""

import uuid

from sqlalchemy import select

from app.core import paths
from app.parsers import mock
from app.storage.models import Demo, Match, Player, Round
from app.workers.jobs import parse_demo_job


def _make_pending_demo(session_factory) -> uuid.UUID:
    s = session_factory()
    demo = Demo(filename="m.dem", path="/tmp/m.dem", status="pending")
    s.add(demo)
    s.commit()
    demo_id = demo.id
    s.close()
    return demo_id


def test_parse_demo_job_mock_success(session_factory, tmp_data, monkeypatch) -> None:
    monkeypatch.setattr("app.workers.jobs.real_parser_available", lambda: False)
    demo_id = _make_pending_demo(session_factory)

    result = parse_demo_job(str(demo_id))
    assert result == "parsed"

    s = session_factory()
    demo = s.get(Demo, demo_id)
    assert demo.status == "parsed"
    assert demo.parsed_at is not None
    assert demo.error is None

    matches = list(s.scalars(select(Match).where(Match.demo_id == demo_id)))
    assert len(matches) == 1
    match_id = matches[0].id
    assert s.scalar(select(Player).where(Player.match_id == match_id)) is not None
    assert s.scalar(select(Round).where(Round.match_id == match_id)) is not None
    s.close()

    # Parquet das tabelas-chave existe (utility/kill matrix/armas dependem delas).
    match_dir = paths.PARQUET_DIR / f"match_id={match_id}"
    for table in ("rounds", "kills", "shots", "grenades", "blinds", "replay_frames"):
        assert (match_dir / f"{table}.parquet").exists()


def test_parse_demo_job_failure_marks_failed(
    session_factory, tmp_data, monkeypatch
) -> None:
    monkeypatch.setattr("app.workers.jobs.real_parser_available", lambda: False)
    demo_id = _make_pending_demo(session_factory)

    def boom(*_args, **_kwargs):
        raise RuntimeError("falha simulada de parsing")

    monkeypatch.setattr(mock, "generate_and_write", boom)

    result = parse_demo_job(str(demo_id))
    assert result == "failed"

    s = session_factory()
    demo = s.get(Demo, demo_id)
    assert demo.status == "failed"
    assert demo.error is not None
    assert "falha simulada" in demo.error
    s.close()


def test_import_enqueues_job(client, monkeypatch) -> None:
    captured: list[str] = []
    monkeypatch.setattr(
        "app.api.routes_demos.enqueue_parse",
        lambda demo_id: captured.append(demo_id),
    )

    resp = client.post(
        "/demos/import",
        files={"file": ("p.dem", b"X", "application/octet-stream")},
    )
    assert resp.status_code == 201
    assert captured == [resp.json()["id"]]
