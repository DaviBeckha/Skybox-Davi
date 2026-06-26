"""Rotas de partidas e metadados."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.schemas import MatchRead, PlayerRead, RoundRead
from app.storage.db import get_db
from app.storage.models import Match, Player, Round

router = APIRouter(prefix="/matches", tags=["matches"])


def get_match_or_404(match_id: uuid.UUID, db: Session) -> Match:
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partida não encontrada.",
        )
    return match


@router.get("", response_model=list[MatchRead])
def list_matches(db: Session = Depends(get_db)) -> list[Match]:
    return list(db.scalars(select(Match).order_by(Match.started_at.desc().nullslast())))


@router.get("/{match_id}", response_model=MatchRead)
def get_match(match_id: uuid.UUID, db: Session = Depends(get_db)) -> Match:
    return get_match_or_404(match_id, db)


@router.get("/{match_id}/summary")
def get_match_summary(match_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    match = get_match_or_404(match_id, db)
    players_count = db.scalar(
        select(func.count()).select_from(Player).where(Player.match_id == match_id)
    )
    rounds_count = db.scalar(
        select(func.count()).select_from(Round).where(Round.match_id == match_id)
    )
    return {
        "id": str(match.id),
        "demo_id": str(match.demo_id),
        "map": match.map,
        "team_a": match.team_a,
        "team_b": match.team_b,
        "score": {"team_a": match.score_a, "team_b": match.score_b},
        "tick_rate": match.tick_rate,
        "started_at": match.started_at.isoformat() if match.started_at else None,
        "players_count": players_count,
        "rounds_count": rounds_count,
    }


@router.get("/{match_id}/rounds", response_model=list[RoundRead])
def list_rounds(match_id: uuid.UUID, db: Session = Depends(get_db)) -> list[Round]:
    get_match_or_404(match_id, db)
    return list(
        db.scalars(
            select(Round).where(Round.match_id == match_id).order_by(Round.round_number.asc())
        )
    )


@router.get("/{match_id}/players", response_model=list[PlayerRead])
def list_players(match_id: uuid.UUID, db: Session = Depends(get_db)) -> list[Player]:
    get_match_or_404(match_id, db)
    return list(
        db.scalars(
            select(Player).where(Player.match_id == match_id).order_by(Player.team, Player.name)
        )
    )
