"""Fila de jobs (RQ + Redis)."""

import logging

import redis
from rq import Queue

from app.core.config import settings

logger = logging.getLogger("cs2-lab.queue")

QUEUE_NAME = "cs2-parsing"
JOB_PATH = "app.workers.jobs.parse_demo_job"


def get_redis() -> redis.Redis:
    return redis.from_url(settings.redis_url)


def get_queue() -> Queue:
    return Queue(QUEUE_NAME, connection=get_redis())


def enqueue_parse(demo_id: str) -> str | None:
    """Enfileira o parsing de uma demo. Retorna o job id, ou None se o Redis
    estiver indisponível (a importação não deve falhar por causa disso)."""
    try:
        job = get_queue().enqueue(JOB_PATH, demo_id)
        logger.info("Job de parsing enfileirado para demo %s (job %s)", demo_id, job.id)
        return job.id
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha ao enfileirar parsing da demo %s: %s", demo_id, exc)
        return None
