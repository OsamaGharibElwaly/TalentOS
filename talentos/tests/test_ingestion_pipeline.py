from pathlib import Path

import pytest

from app.adapters.local_hybrid_index import LocalHybridIndex
from app.adapters.local_queue import LocalAsyncQueue
from app.adapters.local_storage import LocalStorage
from app.adapters.offline_extractor import OfflineExtractor
from app.adapters.sqlite_repo import SQLiteRepository
from app.domain.enums import IngestionStatus
from app.domain.exceptions import QueueLimitError
from app.domain.models import DocumentUpload
from app.services.document_parser import DocumentParser
from app.services.ingestion_service import IngestionService

RESUME = b"""Jane Doe
jane.doe@example.com | +1 555 123 4567
https://linkedin.com/in/janedoe

SUMMARY
Senior engineer with 8 years of experience.

SKILLS
Python, SQL, FastAPI, Docker

EXPERIENCE
Senior Engineer | Acme Corp | 36 months
- Built distributed services
- Led team of 4
Engineer | Beta Inc | 24 months
- Shipped APIs

EDUCATION
BSc Computer Science | State University | 2016
"""


@pytest.fixture()
def pipeline(tmp_path: Path) -> tuple[IngestionService, LocalAsyncQueue, SQLiteRepository, LocalHybridIndex, LocalStorage]:
    repo = SQLiteRepository(tmp_path / "talentos.db")
    storage = LocalStorage(tmp_path / "storage")
    index = LocalHybridIndex(tmp_path / "index.json")
    parser = DocumentParser(storage)
    service = IngestionService(parser, OfflineExtractor(), repo, index)
    queue = LocalAsyncQueue(service.process_job, max_batch_size=50)
    return service, queue, repo, index, storage


def uploads(*items: bytes) -> list[DocumentUpload]:
    return [DocumentUpload(f"resume-{number}.txt", item) for number, item in enumerate(items)]


def test_batch_handles_valid_malformed_and_duplicate(
    pipeline: tuple[IngestionService, LocalAsyncQueue, SQLiteRepository, LocalHybridIndex, LocalStorage]
) -> None:
    service, queue, repo, _, _ = pipeline
    statuses = service.ingest_batch("org-1", uploads(RESUME, b"%PDF-not-a-real-pdf", RESUME), queue)
    assert statuses == [
        IngestionStatus.INDEXED,
        IngestionStatus.FAILED,
        IngestionStatus.INDEXED,
    ]
    assert len(repo.list_candidates("org-1")) == 1


def test_failed_job_records_an_error(
    pipeline: tuple[IngestionService, LocalAsyncQueue, SQLiteRepository, LocalHybridIndex, LocalStorage]
) -> None:
    _, queue, _, _, _ = pipeline
    job_ids = queue.enqueue_batch(
        "org-1", [DocumentUpload("broken.txt", b"!!! no contact !!!")]
    )
    while queue.process_next():
        pass
    job = queue.get_job(job_ids[0])
    assert job is not None
    assert job.status == IngestionStatus.FAILED
    assert job.error


def test_reupload_updates_instead_of_duplicating(
    pipeline: tuple[IngestionService, LocalAsyncQueue, SQLiteRepository, LocalHybridIndex, LocalStorage]
) -> None:
    service, queue, repo, _, storage = pipeline
    service.ingest_batch("org-1", uploads(RESUME), queue)
    first = repo.list_candidates("org-1")[0]
    service.ingest_batch("org-1", uploads(RESUME), queue)
    second = repo.list_candidates("org-1")[0]

    assert len(repo.list_candidates("org-1")) == 1
    assert second.id == first.id
    assert second.file_hash == first.file_hash
    assert second.updated_at >= first.updated_at
    assert storage.get(f"resumes/org-1/{first.file_hash}.txt") == RESUME


def test_same_hash_in_another_org_is_a_separate_candidate(
    pipeline: tuple[IngestionService, LocalAsyncQueue, SQLiteRepository, LocalHybridIndex, LocalStorage]
) -> None:
    service, queue, repo, _, _ = pipeline
    service.ingest_batch("org-1", uploads(RESUME), queue)
    service.ingest_batch("org-2", uploads(RESUME), queue)
    assert len(repo.list_candidates("org-1")) == 1
    assert len(repo.list_candidates("org-2")) == 1
    assert repo.list_candidates("org-1")[0].file_hash == repo.list_candidates("org-2")[0].file_hash


def test_hybrid_index_filters_by_tenant_and_metadata(
    pipeline: tuple[IngestionService, LocalAsyncQueue, SQLiteRepository, LocalHybridIndex, LocalStorage]
) -> None:
    service, queue, repo, index, _ = pipeline
    service.ingest_batch("org-1", uploads(RESUME), queue)
    candidate_id = repo.list_candidates("org-1")[0].id

    assert [hit.doc_id for hit in index.search("org-1", "python engineer")] == [candidate_id]
    assert index.search("org-2", "python engineer") == []
    assert index.search("org-1", "python", metadata_filter={"skills": "python"})
    assert index.search("org-1", "python", metadata_filter={"skills": "rust"}) == []


def test_batch_size_limit_is_enforced(
    pipeline: tuple[IngestionService, LocalAsyncQueue, SQLiteRepository, LocalHybridIndex, LocalStorage]
) -> None:
    _, queue, _, _, _ = pipeline
    with pytest.raises(QueueLimitError):
        queue.enqueue_batch("org-1", uploads(*([RESUME] * 51)))


def test_malformed_docx_does_not_crash_parser(tmp_path: Path) -> None:
    parser = DocumentParser(LocalStorage(tmp_path / "storage"))
    parsed = parser.parse("broken.docx", b"not a zip archive")
    assert parsed.text == ""
    assert parsed.file_hash
