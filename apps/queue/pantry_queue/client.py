"""Queue client for enqueuing tasks"""

import redis
from rq import Queue
from rq.job import Job
from typing import Any, Dict
from pantry_queue.config import settings


class QueueClient:
    """Client for enqueuing and managing tasks"""

    def __init__(self):
        self.redis_conn = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=True,
        )
        self.queue = Queue(
            settings.queue_name,
            connection=self.redis_conn,
            default_timeout=settings.default_timeout,
        )

    def enqueue_ocr_task(
        self,
        receipt_id: int,
        image_path: str,
        user_id: int,
        priority: str = "default",
    ) -> Job:
        """
        Enqueue OCR extraction task for a receipt.

        Args:
            receipt_id: Receipt ID
            image_path: Path to image in MinIO
            user_id: User ID
            priority: Task priority ('high', 'default', 'low')

        Returns:
            RQ Job object
        """
        from pantry_queue.tasks.ocr_tasks import process_receipt_ocr

        job = self.queue.enqueue(
            process_receipt_ocr,
            receipt_id=receipt_id,
            image_path=image_path,
            user_id=user_id,
            result_ttl=settings.result_ttl,
            failure_ttl=settings.failure_ttl,
            job_id=f"ocr-{receipt_id}",  # Prevent duplicates
            at_front=(priority == "high"),
        )

        return job

    def enqueue_batch_ocr(
        self,
        receipt_ids: list[int],
        image_paths: list[str],
        user_id: int,
    ) -> list[Job]:
        """
        Enqueue multiple OCR tasks in batch.

        Args:
            receipt_ids: List of receipt IDs
            image_paths: List of image paths
            user_id: User ID

        Returns:
            List of RQ Job objects
        """
        jobs = []
        for receipt_id, image_path in zip(receipt_ids, image_paths):
            job = self.enqueue_ocr_task(receipt_id, image_path, user_id)
            jobs.append(job)

        return jobs

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get status of a job.

        Args:
            job_id: Job ID (e.g., 'ocr-17')

        Returns:
            Dict with job status information
        """
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)

            return {
                "job_id": job.id,
                "status": job.get_status(),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
                "result": job.result,
                "exc_info": job.exc_info,
                "meta": job.meta,
            }
        except Exception as e:
            return {
                "job_id": job_id,
                "status": "not_found",
                "error": str(e),
            }

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job.

        Args:
            job_id: Job ID

        Returns:
            True if cancelled, False otherwise
        """
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            job.cancel()
            return True
        except Exception:
            return False

    def get_queue_info(self) -> Dict[str, Any]:
        """
        Get queue statistics.

        Returns:
            Dict with queue information
        """
        return {
            "name": self.queue.name,
            "count": len(self.queue),  # Pending jobs
            "started_jobs": self.queue.started_job_registry.count,
            "finished_jobs": self.queue.finished_job_registry.count,
            "failed_jobs": self.queue.failed_job_registry.count,
            "scheduled_jobs": self.queue.scheduled_job_registry.count,
            "deferred_jobs": self.queue.deferred_job_registry.count,
        }

    def clear_failed_jobs(self) -> int:
        """Clear all failed jobs from the queue."""
        count = self.queue.failed_job_registry.count
        self.queue.failed_job_registry.cleanup()
        return count


# Singleton instance
queue_client = QueueClient()
