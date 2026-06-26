"""Rotas de mapas e assets de radar."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.analytics.maps import list_maps, load_metadata, radar_path

router = APIRouter(prefix="/maps", tags=["maps"])


@router.get("")
def maps() -> list[dict]:
    return list_maps()


@router.get("/{map_name}/metadata")
def metadata(map_name: str) -> dict:
    try:
        return load_metadata(map_name)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapa não encontrado.",
        ) from exc


@router.get("/{map_name}/radar")
def radar(map_name: str) -> FileResponse:
    try:
        path = radar_path(map_name)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Radar não encontrado.",
        ) from exc
    return FileResponse(path, media_type="image/png")
