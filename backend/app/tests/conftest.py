"""Fixtures de teste: cliente FastAPI com banco SQLite em memória e dir de demos temporário."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import paths
from app.main import app
from app.storage.db import Base, get_db


@pytest.fixture()
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db() -> Iterator[Session]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    # Redireciona a escrita de demos para um diretório temporário.
    monkeypatch.setattr(paths, "RAW_DEMOS_DIR", tmp_path / "raw_demos")
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
