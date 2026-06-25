"""Tipos internos produzidos por parsers reais e mock.

Nenhum adapter expõe tipos de awpy/demoparser2 para o restante da aplicação. A
fronteira interna é `ParsedDemo`: metadados relacionais + linhas canônicas dos
Parquet definidos em `schema.PARQUET_SCHEMAS`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PlayerMeta:
    steam_id: str
    name: str
    team: str
    starting_side: str


@dataclass(frozen=True)
class RoundMeta:
    round_number: int
    winner: str
    reason: str
    start_tick: int
    end_tick: int


@dataclass(frozen=True)
class MatchMeta:
    map: str
    team_a: str | None
    team_b: str | None
    score_a: int | None
    score_b: int | None
    tick_rate: int | None
    started_at: datetime | None
    players: list[PlayerMeta]
    rounds: list[RoundMeta]


@dataclass(frozen=True)
class ParsedDemo:
    match: MatchMeta
    tables: dict[str, list[dict]]
