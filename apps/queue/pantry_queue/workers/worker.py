"""RQ Worker process"""

import redis
from rq import Worker
from pantry_queue.config import settings


def run_worker():
    """Run RQ worker process"""
    redis_conn = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password,
        decode_responses=True,
    )

    worker_name = settings.worker_name or "worker-1"

    print(f"[Worker] Starting RQ worker: {worker_name}")
    print(f"[Worker] Queue: {settings.queue_name}")
    print(f"[Worker] Redis: {settings.redis_host}:{settings.redis_port}")

    worker = Worker(
        [settings.queue_name],
        connection=redis_conn,
        name=worker_name,
    )

    # Run worker
    worker.work(burst=settings.burst_mode)


if __name__ == "__main__":
    run_worker()
