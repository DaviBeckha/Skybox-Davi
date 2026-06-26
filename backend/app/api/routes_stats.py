"""Rotas de stats/analytics."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analytics.economy import build_economy
from app.analytics.maps import load_metadata
from app.analytics.matchups import build_matchups
from app.analytics.player_stats import build_player_stats
from app.analytics.positions import build_death_positions
from app.analytics.sites import build_bombsites
from app.analytics.utility import build_utility
from app.analytics.weapons import build_weapons
from app.api.routes_matches import get_match_or_404
from app.storage.db import get_db

router = APIRouter(prefix="/matches", tags=["stats"])


@router.get("/{match_id}/stats/player")
def player_stats(match_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    get_match_or_404(match_id, db)
    return build_player_stats(str(match_id))


@router.get("/{match_id}/stats/economy")
def economy_stats(match_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    get_match_or_404(match_id, db)
    return build_economy(str(match_id))


@router.get("/{match_id}/stats/weapons")
def weapon_stats(match_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    get_match_or_404(match_id, db)
    return build_weapons(str(match_id))


@router.get("/{match_id}/stats/utility")
def utility_stats(match_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    get_match_or_404(match_id, db)
    return build_utility(str(match_id))


@router.get("/{match_id}/stats/matchups")
def matchups(match_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    get_match_or_404(match_id, db)
    return build_matchups(str(match_id))


@router.get("/{match_id}/stats/death-positions")
def death_positions(
    match_id: uuid.UUID,
    player: str,
    db: Session = Depends(get_db),
) -> dict:
    match = get_match_or_404(match_id, db)
    metadata = load_metadata(match.map)
    return build_death_positions(str(match_id), match.map, player, metadata)


@router.get("/{match_id}/stats/bombsites")
def bombsites(match_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    match = get_match_or_404(match_id, db)
    return build_bombsites(str(match_id), match.map)
