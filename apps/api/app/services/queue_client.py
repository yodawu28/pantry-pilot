"""
Simple queue client wrapper for API service.

This provides a lightweight client without needing the full queue package.
"""

import redis
from rq import Queue
from rq.job import Job
from typing import Dict, Any, Optional

from app.config import settings


class SimpleQueueClient:
    """Lightweight queue client for API service"""

    def __init__(self):
        try:
            self.redis_conn = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                decode_responses=True,
            )
            self.queue = Queue("pantry-pilot", connection=self.redis_conn)
            self.available = True
        except Exception as e:
            print(f"[Queue Client] Redis not available: {e}")
            self.available = False

    def enqueue_ocr_task(
        self, receipt_id: int, image_path: str, user_id: int
    ) -> Optional[Job]:
        """Enqueue OCR task by function path (worker will resolve it)"""
        if not self.available:
            return None

        try:
            # Enqueue by function path - worker will import and execute
            # Using function path string so API doesn't need the queue package
            job = self.queue.enqueue(
                "pantry_queue.tasks.ocr_tasks.process_receipt_ocr",
                receipt_id=receipt_id,
                image_path=image_path,
                user_id=user_id,
                job_id=f"ocr-{receipt_id}",
            )
            return job
        except Exception as e:
            print(f"[Queue Client] Enqueue failed: {e}")
            raise
        return job

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status"""
        if not self.available:
            return {"job_id": job_id, "status": "unavailable"}

        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            return {
                "job_id": job.id,
                "status": job.get_status(),
                "result": job.result,
            }
        except Exception:
            return {"job_id": job_id, "status": "not_found"}

    def get_queue_info(self) -> Dict[str, Any]:
        """Get queue stats"""
        if not self.available:
            return {"available": False}

        return {
            "available": True,
            "count": len(self.queue),
            "name": self.queue.name,
        }


# Singleton instance
simple_queue_client = SimpleQueueClient()
