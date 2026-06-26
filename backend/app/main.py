"""Aplicação FastAPI do cs2-lab (backend mínimo)."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import (
    routes_demos,
    routes_maps,
    routes_matches,
    routes_replay,
    routes_stats,
)
from app.core.config import settings
from app.core.paths import ensure_dirs
from app.models.schemas import HealthResponse
from app.storage.db import engine

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("cs2-lab")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    ensure_dirs()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Conexão com o PostgreSQL OK")
    except Exception as exc:  # noqa: BLE001 — apenas logamos; não derrubamos a API
        logger.warning("Falha ao conectar no PostgreSQL no startup: %s", exc)
    yield


app = FastAPI(title=settings.api_title, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_demos.router)
app.include_router(routes_matches.router)
app.include_router(routes_replay.router)
app.include_router(routes_stats.router)
app.include_router(routes_maps.router)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")
