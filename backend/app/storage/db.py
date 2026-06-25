"""Engine e sessão SQLAlchemy apontando para o PostgreSQL."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Base declarativa para os modelos ORM."""


engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Iterator[Session]:
    """Dependência FastAPI: fornece uma sessão e a fecha ao final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
