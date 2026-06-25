"""Fixtures de teste.

Os testes usam **PostgreSQL exclusivamente** (sem SQLite): um banco de teste
dedicado (`cs2_lab_test`) no mesmo container, criado a partir da `DATABASE_URL`.
Requer o Postgres no ar (`docker compose up -d postgres`).
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.engine import URL, Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core import paths
from app.core.config import settings
from app.main import app
from app.storage import db
from app.storage.db import Base, get_db

TEST_DB_NAME = "cs2_lab_test"
_TABLES = "demos, matches, players, rounds"


def _test_db_url() -> URL:
    # Objeto URL (não str): str(url) mascara a senha como "***".
    return make_url(settings.database_url).set(database=TEST_DB_NAME)


@pytest.fixture(scope="session")
def _engine() -> Iterator[Engine]:
    # Cria o banco de teste, se necessário, conectando à database de manutenção.
    admin_url = make_url(settings.database_url).set(database="postgres")
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"),
            {"n": TEST_DB_NAME},
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    admin_engine.dispose()

    engine = create_engine(_test_db_url())
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def session_factory(_engine: Engine, monkeypatch) -> sessionmaker:
    """Factory de sessões ligada ao banco de teste. Limpa as tabelas e aponta
    `db.SessionLocal` para o banco de teste (usado pelos jobs)."""
    with _engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {_TABLES} CASCADE"))
    factory = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(db, "SessionLocal", factory)
    return factory


@pytest.fixture()
def tmp_data(tmp_path, monkeypatch) -> "object":
    """Redireciona os diretórios de dados para um tmp."""
    raw = tmp_path / "raw_demos"
    parquet = tmp_path / "parquet"
    duckdb = tmp_path / "duckdb"
    for d in (raw, parquet, duckdb):
        d.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(paths, "RAW_DEMOS_DIR", raw)
    monkeypatch.setattr(paths, "PARQUET_DIR", parquet)
    monkeypatch.setattr(paths, "DUCKDB_DIR", duckdb)
    monkeypatch.setattr(paths, "DUCKDB_PATH", duckdb / "cs2_lab.duckdb")
    return tmp_path


@pytest.fixture()
def db_session(session_factory: sessionmaker) -> Iterator[Session]:
    s = session_factory()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture()
def client(
    session_factory: sessionmaker, tmp_data, monkeypatch
) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    # Por padrão, não dependemos do Redis nos testes de API.
    monkeypatch.setattr("app.api.routes_demos.enqueue_parse", lambda _demo_id: None)
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
