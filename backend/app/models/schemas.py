"""Schemas Pydantic dos metadados, seguindo o contrato de dados.

Nomes em snake_case (a conversão para camelCase acontece no frontend).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str


class DemoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    path: str
    status: str
    created_at: datetime
    parsed_at: datetime | None = None
    error: str | None = None


class MatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    demo_id: uuid.UUID
    map: str
    team_a: str | None = None
    team_b: str | None = None
    score_a: int | None = None
    score_b: int | None = None
    started_at: datetime | None = None
    tick_rate: int | None = None


class PlayerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: uuid.UUID
    steam_id: str
    name: str | None = None
    team: str | None = None


class RoundRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: uuid.UUID
    round_number: int
    winner: str | None = None
    reason: str | None = None
    start_tick: int | None = None
    end_tick: int | None = None
