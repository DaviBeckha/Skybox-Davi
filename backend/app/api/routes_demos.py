"""Rotas de demos: importação, listagem e consulta.

Esta phase cria o registro em `status="pending"`. O job de parsing e as
transições de status são da Phase 06.
"""

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import paths
from app.models.schemas import DemoRead
from app.storage.db import get_db
from app.storage.models import Demo
from app.workers.queue import enqueue_parse

router = APIRouter(prefix="/demos", tags=["demos"])


@router.post("/import", response_model=DemoRead, status_code=status.HTTP_201_CREATED)
def import_demo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Demo:
    original_name = file.filename or ""
    if not original_name.lower().endswith(".dem"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas arquivos .dem são aceitos.",
        )

    paths.RAW_DEMOS_DIR.mkdir(parents=True, exist_ok=True)
    demo_id = uuid.uuid4()
    # Nome em disco único (evita colisão quando o mesmo filename é importado de novo);
    # o nome original é preservado em `filename`.
    dest = paths.RAW_DEMOS_DIR / f"{demo_id}.dem"
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    demo = Demo(
        id=demo_id,
        filename=Path(original_name).name,
        path=str(dest),
        status="pending",
    )
    db.add(demo)
    db.commit()
    db.refresh(demo)

    # Enfileira o parsing (assíncrono). Não bloqueia a resposta; se o Redis
    # estiver indisponível, a demo permanece `pending` e pode ser reprocessada.
    enqueue_parse(str(demo.id))
    return demo


@router.get("", response_model=list[DemoRead])
def list_demos(db: Session = Depends(get_db)) -> list[Demo]:
    return list(db.scalars(select(Demo).order_by(Demo.created_at.desc())))


@router.get("/{demo_id}", response_model=DemoRead)
def get_demo(demo_id: uuid.UUID, db: Session = Depends(get_db)) -> Demo:
    demo = db.get(Demo, demo_id)
    if demo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo não encontrada.",
        )
    return demo
