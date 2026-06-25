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
def client(_engine: Engine, tmp_path, monkeypatch) -> Iterator[TestClient]:
    # Estado limpo a cada teste.
    with _engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {_TABLES} CASCADE"))

    session_local = sessionmaker(bind=_engine, autoflush=False, autocommit=False)

    def override_get_db() -> Iterator[Session]:
        db = session_local()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(paths, "RAW_DEMOS_DIR", tmp_path / "raw_demos")
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
