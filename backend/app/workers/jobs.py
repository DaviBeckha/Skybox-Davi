"""Job de parsing de demo (RQ).

Ciclo de status (coluna `demos.status`):
    pending -> parsing -> parsed
    pending -> parsing -> failed
"""

import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.core import paths
from app.parsers import mock, parse_real_demo, real_parser_available
from app.parsers.result import MatchMeta
from app.storage import db, duckdb
from app.storage.models import Demo, Match, Player, Round
from app.storage.parquet import write_parquet_tables

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
    for player in meta.players:
        session.add(
            Player(
                match_id=match_id,
                steam_id=player.steam_id,
                name=player.name,
                team=player.team,
            )
        )
    for round_meta in meta.rounds:
        session.add(
            Round(
                match_id=match_id,
                round_number=round_meta.round_number,
                winner=round_meta.winner,
                reason=round_meta.reason,
                start_tick=round_meta.start_tick,
                end_tick=round_meta.end_tick,
            )
        )


def parse_demo_job(demo_id: str) -> str:
    """Executa o parsing de uma demo (real quando disponivel; senao mock)."""
    session = db.SessionLocal()
    try:
        demo = session.get(Demo, uuid.UUID(demo_id))
        if demo is None:
            logger.error("Demo %s nao encontrada", demo_id)
            return "not_found"

        demo.status = "parsing"
        session.commit()
        logger.info("Parsing iniciado (parsing) para demo %s", demo_id)

        try:
            paths.ensure_dirs()
            match_id = uuid.uuid4()
            if real_parser_available():
                logger.info("Parser real disponivel: usando awpy/demoparser2 para %s", demo_id)
                parsed = parse_real_demo(Path(demo.path), match_id=str(match_id))
                write_parquet_tables(str(match_id), parsed.tables, paths.PARQUET_DIR)
                meta = parsed.match
            else:
                logger.info("Parser real ausente: usando mock fallback para %s", demo_id)
                meta = mock.generate_and_write(str(match_id), demo.path, paths.PARQUET_DIR)

            connection = duckdb.refresh_views(paths.PARQUET_DIR, paths.DUCKDB_PATH)
            connection.close()

            _persist_metadata(session, demo, match_id, meta)
            demo.status = "parsed"
            demo.parsed_at = datetime.now(UTC)
            demo.error = None
            session.commit()
            logger.info("Parsing concluido (parsed) para demo %s", demo_id)
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
