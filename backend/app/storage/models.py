"""Modelos ORM dos metadados (PostgreSQL).

Schemas seguem o contrato de dados (contracts/_shared/data-contract.md, seção 1):
demos, matches, players, rounds.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Text
from sqlalchemy import Uuid as SAUuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.storage.db import Base


class Demo(Base):
    __tablename__ = "demos"

    id: Mapped[uuid.UUID] = mapped_column(SAUuid, primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    parsed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    matches: Mapped[list[Match]] = relationship(back_populates="demo")


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(SAUuid, primary_key=True, default=uuid.uuid4)
    demo_id: Mapped[uuid.UUID] = mapped_column(
        SAUuid, ForeignKey("demos.id"), nullable=False
    )
    map: Mapped[str] = mapped_column(Text, nullable=False)
    team_a: Mapped[str | None] = mapped_column(Text, nullable=True)
    team_b: Mapped[str | None] = mapped_column(Text, nullable=True)
    score_a: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_b: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tick_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)

    demo: Mapped[Demo] = relationship(back_populates="matches")
    players: Mapped[list[Player]] = relationship(back_populates="match")
    rounds: Mapped[list[Round]] = relationship(back_populates="match")


class Player(Base):
    __tablename__ = "players"

    match_id: Mapped[uuid.UUID] = mapped_column(
        SAUuid, ForeignKey("matches.id"), primary_key=True
    )
    steam_id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    team: Mapped[str | None] = mapped_column(Text, nullable=True)

    match: Mapped[Match] = relationship(back_populates="players")


class Round(Base):
    __tablename__ = "rounds"

    match_id: Mapped[uuid.UUID] = mapped_column(
        SAUuid, ForeignKey("matches.id"), primary_key=True
    )
    round_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    winner: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_tick: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    end_tick: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    match: Mapped[Match] = relationship(back_populates="rounds")
