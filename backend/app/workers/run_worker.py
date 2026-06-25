"""Entrypoint do worker RQ.

Usa `SimpleWorker` (sem fork) para funcionar também no Windows.
Iniciar com: `uv run python -m app.workers.run_worker`
"""

import logging

from rq import Queue, SimpleWorker

from app.core.config import settings
from app.workers.queue import QUEUE_NAME, get_redis


def main() -> None:
    logging.basicConfig(level=settings.log_level)
    conn = get_redis()
    worker = SimpleWorker([Queue(QUEUE_NAME, connection=conn)], connection=conn)
    worker.work()


if __name__ == "__main__":
    main()
