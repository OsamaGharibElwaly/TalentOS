from __future__ import annotations

import threading
from collections.abc import Callable
from uuid import uuid4

from app.domain.enums import IngestionStatus
from app.domain.exceptions import QueueLimitError
from app.domain.models import DocumentUpload, QueuedJob
from app.ports.queue import QueuePort


class LocalAsyncQueue(QueuePort):
    """In-process queue: enqueue now, process jobs one at a time later."""

    def __init__(
        self, processor: Callable[[QueuedJob], None], *, max_batch_size: int = 50
    ) -> None:
        self._processor = processor
        self._max_batch_size = max_batch_size
        self._jobs: dict[str, QueuedJob] = {}
        self._order: list[str] = []
        self._lock = threading.Lock()

    def enqueue(self, tenant_id: str, upload: DocumentUpload) -> str:
        job = QueuedJob(
            id=str(uuid4()),
            tenant_id=tenant_id,
            upload=upload,
            status=IngestionStatus.QUEUED,
        )
        with self._lock:
            self._jobs[job.id] = job
            self._order.append(job.id)
        return job.id

    def enqueue_batch(
        self, tenant_id: str, uploads: list[DocumentUpload]
    ) -> list[str]:
        if len(uploads) > self._max_batch_size:
            raise QueueLimitError(
                f"batch of {len(uploads)} exceeds the {self._max_batch_size}-file limit"
            )
        return [self.enqueue(tenant_id, upload) for upload in uploads]

    def process_next(self) -> bool:
        with self._lock:
            job_id = next(
                (
                    item_id
                    for item_id in self._order
                    if self._jobs[item_id].status == IngestionStatus.QUEUED
                ),
                None,
            )
            if job_id is None:
                return False
            job = self._jobs[job_id]
            job.status = IngestionStatus.PARSING

        try:
            self._processor(job)
        except Exception as exc:  # one bad file must not abort the batch
            with self._lock:
                job.status = IngestionStatus.FAILED
                job.error = str(exc) or type(exc).__name__
        else:
            with self._lock:
                job.status = IngestionStatus.INDEXED
        return True

    def get_job(self, job_id: str) -> QueuedJob | None:
        return self._jobs.get(job_id)

    def get_job_status(self, job_id: str) -> IngestionStatus:
        job = self.get_job(job_id)
        if job is None:
            raise KeyError(job_id)
        return job.status
