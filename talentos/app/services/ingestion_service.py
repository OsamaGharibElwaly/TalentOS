from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.domain.enums import IngestionStatus
from app.domain.models import CandidateRecord, DocumentUpload, QueuedJob
from app.ports.inference import InferencePort
from app.ports.queue import QueuePort
from app.ports.repositories import RepositoryPort
from app.ports.vector_index import VectorIndexPort
from app.services.document_parser import DocumentParser


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class IngestionService:
    """Parses, validates, persists and indexes one queued resume at a time."""

    def __init__(
        self,
        parser: DocumentParser,
        extractor: InferencePort,
        repo: RepositoryPort,
        index: VectorIndexPort,
    ) -> None:
        self._parser = parser
        self._extractor = extractor
        self._repo = repo
        self._index = index

    def process_job(self, job: QueuedJob) -> CandidateRecord:
        parsed = self._parser.parse(
            job.upload.filename, job.upload.raw_bytes, tenant_id=job.tenant_id
        )
        profile = self._extractor.extract_profile(parsed.text, parsed.chunks)
        existing = self._repo.get_candidate_by_hash(job.tenant_id, parsed.file_hash)
        now = _now()
        record = CandidateRecord(
            id=existing.id if existing is not None else str(uuid4()),
            tenant_id=job.tenant_id,
            file_hash=parsed.file_hash,
            filename=job.upload.filename,
            storage_key=parsed.storage_key,
            profile=profile,
            created_at=existing.created_at if existing is not None else now,
            updated_at=now,
        )
        saved = self._repo.upsert_candidate(record)
        self._index.upsert(
            doc_id=saved.id,
            tenant_id=job.tenant_id,
            text=parsed.text,
            metadata={
                "filename": saved.filename,
                "file_hash": saved.file_hash,
                "full_name": profile.full_name,
                "skills": profile.skills,
            },
        )
        return saved

    def ingest_batch(
        self, tenant_id: str, uploads: list[DocumentUpload], queue: QueuePort
    ) -> list[IngestionStatus]:
        job_ids = queue.enqueue_batch(tenant_id, uploads)
        while queue.process_next():
            pass
        return [queue.get_job_status(job_id) for job_id in job_ids]
