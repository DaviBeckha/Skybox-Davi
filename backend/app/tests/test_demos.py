"""Testes de importação/listagem/consulta de demos (Phase 05)."""

import uuid
from pathlib import Path


def test_import_rejects_non_dem(client) -> None:
    resp = client.post(
        "/demos/import",
        files={"file": ("notas.txt", b"conteudo", "text/plain")},
    )
    assert resp.status_code == 400


def test_import_dem_creates_pending_and_copies_file(client) -> None:
    resp = client.post(
        "/demos/import",
        files={"file": ("partida1.dem", b"FAKEDEMODATA", "application/octet-stream")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert data["filename"] == "partida1.dem"
    assert data["parsed_at"] is None
    assert data["error"] is None
    # arquivo copiado para o diretório de demos
    assert Path(data["path"]).exists()


def test_list_and_get_demo(client) -> None:
    created = client.post(
        "/demos/import",
        files={"file": ("partida2.dem", b"X", "application/octet-stream")},
    ).json()

    listed = client.get("/demos")
    assert listed.status_code == 200
    items = listed.json()
    assert len(items) == 1
    assert items[0]["id"] == created["id"]

    one = client.get(f"/demos/{created['id']}")
    assert one.status_code == 200
    assert one.json()["id"] == created["id"]


def test_get_demo_404(client) -> None:
    resp = client.get(f"/demos/{uuid.uuid4()}")
    assert resp.status_code == 404
