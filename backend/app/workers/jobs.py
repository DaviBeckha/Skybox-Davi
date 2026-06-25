"""Job de parsing de demo (RQ).

Ciclo de status (coluna `demos.status`):
    pending → parsing → parsed
    pending → parsing → failed
"""

import logging
import uuid
from datetime import UTC, datetime

from app.core import paths
from app.parsers import mock, real_parser_available
from app.parsers.mock import MatchMeta
from app.storage import db
from app.storage.models import Demo, Match, Player, Round

logger = logging.getLogger("cs2-lab.jobs")


def _persist_metadata(session, demo: Demo, match_id: uuid.UUID, meta: MatchMeta) -> None:
    match = Match(
        id=match_id,
        demo_id=demo.id,
        map=meta.map,
        team_a=meta.team_a,
        team_b=meta.team_b,
        score_a=meta.score_a,
        score_b=meta.score_b,
        started_at=meta.started_at,
        tick_rate=meta.tick_rate,
    )
    session.add(match)
    for p in meta.players:
        session.add(
            Player(match_id=match_id, steam_id=p.steam_id, name=p.name, team=p.team)
        )
    for r in meta.rounds:
        session.add(
            Round(
                match_id=match_id,
                round_number=r.round_number,
                winner=r.winner,
                reason=r.reason,
                start_tick=r.start_tick,
                end_tick=r.end_tick,
            )
        )


def parse_demo_job(demo_id: str) -> str:
    """Executa o parsing de uma demo (real quando disponível; senão mock)."""
    session = db.SessionLocal()
    try:
        demo = session.get(Demo, uuid.UUID(demo_id))
        if demo is None:
            logger.error("Demo %s não encontrada", demo_id)
            return "not_found"

        demo.status = "parsing"
        session.commit()
        logger.info("Parsing iniciado (parsing) para demo %s", demo_id)

        try:
            paths.ensure_dirs()
            match_id = uuid.uuid4()
            if real_parser_available():
                # Phase 07 implementa o parser real.
                raise NotImplementedError("parser real não implementado")
            logger.info("Parser real ausente — usando mock fallback para %s", demo_id)
            meta = mock.generate_and_write(str(match_id), demo.path, paths.PARQUET_DIR)

            _persist_metadata(session, demo, match_id, meta)
            demo.status = "parsed"
            demo.parsed_at = datetime.now(UTC)
            demo.error = None
            session.commit()
            logger.info("Parsing concluído (parsed) para demo %s", demo_id)
            return "parsed"
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            demo = session.get(Demo, uuid.UUID(demo_id))
            if demo is not None:
                demo.status = "failed"
                demo.error = str(exc)
                session.commit()
            logger.exception("Parsing falhou (failed) para demo %s", demo_id)
            return "failed"
    finally:
        session.close()
