"""Rotas de replay e heatmap."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.analytics.heatmaps import build_heatmap
from app.analytics.maps import load_metadata
from app.analytics.replay_frames import build_replay
from app.api.routes_matches import get_match_or_404
from app.storage.db import get_db

router = APIRouter(prefix="/matches", tags=["replay"])


@router.get("/{match_id}/replay")
def replay(
    match_id: uuid.UUID,
    round: int = Query(1, ge=1),  # noqa: A002 - nome no contrato HTTP
    sample_rate: int = Query(8, ge=1),
    db: Session = Depends(get_db),
) -> dict:
    match = get_match_or_404(match_id, db)
    metadata = load_metadata(match.map)
    return build_replay(
        str(match_id),
        match.map,
        match.tick_rate,
        round,
        sample_rate,
        metadata,
    )


@router.get("/{match_id}/heatmap")
def heatmap(
    match_id: uuid.UUID,
    type: str = Query(...),  # noqa: A002 - nome no contrato HTTP
    player: str | None = None,
    team: str | None = None,
    side: str | None = None,
    round_range: str | None = None,
    weapon: str | None = None,
    grenade_type: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    match = get_match_or_404(match_id, db)
    metadata = load_metadata(match.map)
    try:
        return build_heatmap(
            str(match_id),
            match.map,
            type,
            metadata,
            player=player,
            team=team,
            side=side,
            round_range=round_range,
            weapon=weapon,
            grenade_type=grenade_type,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
