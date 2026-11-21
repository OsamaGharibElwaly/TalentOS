from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import asdict
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from app.adapters.local_hybrid_index import LocalHybridIndex
from app.adapters.local_storage import LocalStorage
from app.adapters.sqlite_repo import SQLiteRepository
from app.api.deps import (
    get_auth_service,
    get_index,
    get_repo,
    get_settings,
    get_storage,
)
from app.api.main import create_app
from app.config import Settings
from app.domain.enums import ApplicationStage, Permission, Role
from app.domain.models import (
    Application,
    CandidateProfile,
    CandidateRecord,
    CriterionScore,
    ScoringResult,
    User,
)
from app.middleware.rate_limiter import RateLimiter, bucket_for
from app.services.auth_service import AuthService
from app.services.scoring_service import _criteria_index

TENANT = "org-1"
RESUME = b"Alice Rivera\nalice@example.com\n8 years building Python services.\n"


def _profile(index: int) -> CandidateProfile:
    return CandidateProfile(
        full_name=f"Candidate {index}",
        email=f"candidate{index}@example.com",
        phone="+15551234567",
        links=[],
        total_experience_years=float(index % 20),
        skills=["python"],
        experience_entries=[],
        education=[],
        raw_chunks=[],
        raw_text="Built Python services",
    )


def _seed(repo: SQLiteRepository, count: int = 200) -> None:
    for index in range(count):
        candidate_id = f"c{index}"
        repo.upsert_candidate(
            CandidateRecord(
                id=candidate_id,
                tenant_id=TENANT,
                file_hash=f"hash-{index}",
                filename=f"resume-{index}.txt",
                storage_key=f"key-{index}",
                profile=_profile(index),
                created_at="2026-01-01T00:00:00+00:00",
                updated_at="2026-01-01T00:00:00+00:00",
            )
        )
        application_id = f"a{index}"
        repo.add_application(
            Application(
                application_id,
                TENANT,
                candidate_id,
                f"j{index % 5}",
                ApplicationStage.NEW,
                "2026-01-01T00:00:00+00:00",
            )
        )
        repo.save_scoring_result(
            ScoringResult(
                application_id=application_id,
                candidate_id=candidate_id,
                composite_score=(index % 100) / 100,
                criterion_scores=[
                    CriterionScore("c1", "Engineering", 1.0, index % 100, "evidence", [], 1.0)
                ],
                gaps_and_probes=[],
                blind_mode=False,
            )
        )


@pytest.fixture()
def harness(tmp_path: Path) -> Iterator[tuple[SQLiteRepository, TestClient]]:
    repo = SQLiteRepository(tmp_path / "talentos.db")
    for user_id, role in (
        ("admin", Role.ADMIN),
        ("recruiter", Role.RECRUITER),
        ("viewer", Role.VIEWER),
        *((f"r{index}", Role.RECRUITER) for index in range(6)),
    ):
        repo.add_user(User(user_id, TENANT, role))
    storage = LocalStorage(tmp_path / "storage")
    index = LocalHybridIndex(tmp_path / "index.json")
    settings = Settings(
        data_dir=tmp_path,
        db_path=tmp_path / "talentos.db",
        storage_dir=tmp_path / "storage",
        rubric_tolerance=1e-6,
        index_path=tmp_path / "index.json",
        inference_backend="offline",
        max_batch_size=50,
    )
    app = create_app()
    app.dependency_overrides[get_repo] = lambda: repo
    app.dependency_overrides[get_auth_service] = lambda: AuthService(repo)
    app.dependency_overrides[get_storage] = lambda: storage
    app.dependency_overrides[get_index] = lambda: index
    app.dependency_overrides[get_settings] = lambda: settings
    client = TestClient(app)
    try:
        yield repo, client
    finally:
        app.dependency_overrides.clear()
        repo.close()


def _headers(user_id: str) -> dict[str, str]:
    return {"X-User-Id": user_id, "X-Tenant-Id": TENANT}


def test_sqlite_pragmas_and_composite_indexes_are_installed(
    harness: tuple[SQLiteRepository, TestClient],
) -> None:
    repo, _ = harness
    pragmas = {
        "journal_mode": repo._conn.execute("PRAGMA journal_mode").fetchone()[0],
        "synchronous": repo._conn.execute("PRAGMA synchronous").fetchone()[0],
        "busy_timeout": repo._conn.execute("PRAGMA busy_timeout").fetchone()[0],
    }
    assert pragmas["journal_mode"] == "wal"
    assert pragmas["synchronous"] == 1
    assert pragmas["busy_timeout"] == 5000

    indexes = {
        str(row["name"])
        for row in repo._conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'"
        ).fetchall()
    }
    for name in (
        "idx_scoring_tenant_job_score",
        "idx_applications_tenant_stage",
        "idx_candidates_tenant_hash",
    ):
        assert name in indexes, name


def test_bulk_scoring_lookup_removes_n_plus_one_on_large_lists(
    harness: tuple[SQLiteRepository, TestClient],
) -> None:
    repo, client = harness
    _seed(repo, 200)

    statements: list[str] = []
    original = repo.get_scoring_result

    def spy(application_id: str) -> object:
        statements.append(application_id)
        return original(application_id)

    repo.get_scoring_result = spy  # type: ignore[method-assign]
    started = time.perf_counter()
    response = client.get("/frontend/candidates", headers=_headers("recruiter"))
    elapsed = time.perf_counter() - started

    assert response.status_code == 200
    assert statements == []
    rows = response.json()
    assert len(rows) == 200
    assert all(item["applications"][0]["scoring"] is not None for item in rows)
    assert elapsed < 5.0, elapsed


def test_scoring_result_round_trip_and_legacy_migration(tmp_path: Path) -> None:
    db = tmp_path / "legacy.db"
    connection = sqlite3.connect(str(db))
    connection.execute(
        "CREATE TABLE scoring_results (application_id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
    )
    legacy = ScoringResult("a1", "c1", 0.75, [], [], False)
    connection.execute(
        "INSERT INTO scoring_results VALUES (?, ?)",
        ("a1", json.dumps(asdict(legacy))),
    )
    connection.commit()
    connection.close()

    repo = SQLiteRepository(db)
    columns = {
        str(row["name"])
        for row in repo._conn.execute("PRAGMA table_info(scoring_results)").fetchall()
    }
    assert {"tenant_id", "job_id", "total_score"} <= columns
    assert repo.get_scoring_result("a1") == legacy
    assert repo.list_scoring_results(TENANT) == {}
    repo.close()


def test_rate_limiter_slides_and_expires(tmp_path: Path) -> None:
    limiter = RateLimiter(limit=2, window_seconds=10.0)
    assert limiter.check("upload:user", now=0.0) is True
    assert limiter.check("upload:user", now=1.0) is True
    assert limiter.check("upload:user", now=2.0) is False
    assert limiter.check("upload:user", now=10.5) is True
    assert limiter.pending("upload:user") == 2
    assert bucket_for("/frontend/ingest") == ("upload", 5)
    assert bucket_for("/frontend/account") == ("signup", 10)
    assert bucket_for("/search/talent") == ("search", 60)
    assert bucket_for("/health") is None


def test_http_rate_limit_throttles_repeated_uploads(
    harness: tuple[SQLiteRepository, TestClient],
) -> None:
    _, client = harness
    statuses = [
        client.post(
            "/frontend/ingest",
            files=[("files", ("resume.txt", RESUME, "text/plain"))],
            headers=_headers("recruiter"),
        ).status_code
        for _ in range(6)
    ]
    assert statuses == [201, 201, 201, 201, 201, 429]


def test_upload_validation_rejects_unsafe_inputs(
    harness: tuple[SQLiteRepository, TestClient],
) -> None:
    _, client = harness
    cases = [
        ("../escape.txt", RESUME, "invalid filename"),
        ("payload.exe", RESUME, "unsupported file type"),
        ("fake.pdf", RESUME, "file content does not match extension"),
        ("empty.txt", b"", "empty file"),
        ("large.txt", b"x" * (10 * 1024 * 1024 + 1), "file too large"),
        ("binary.txt", b"\xff\xfe\x00", "file content is not valid text"),
    ]
    for index, (name, payload, expected) in enumerate(cases):
        response = client.post(
            "/frontend/ingest",
            files=[("files", (name, payload, "application/octet-stream"))],
            headers=_headers(f"r{index}"),
        )
        assert response.status_code == 201
        assert response.json()[0]["error"] == expected, name
        assert response.json()[0]["status"] == "FAILED"


def test_security_headers_cover_public_and_sensitive_routes(
    harness: tuple[SQLiteRepository, TestClient],
) -> None:
    _, client = harness
    for path, headers in (
        ("/health", _headers("viewer")),
        ("/frontend/session", _headers("viewer")),
        ("/api/v1/telemetry/summary", _headers("admin")),
    ):
        response = client.get(path, headers=headers)
        assert response.headers["Content-Security-Policy"].startswith("default-src 'self'")
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "camera=()" in response.headers["Permissions-Policy"]
        if path != "/health":
            assert response.headers["Cache-Control"] == "no-store"


def test_rubric_index_cache_is_bounded_and_value_addressed() -> None:
    from app.domain.models import RubricCriterion

    criteria = (RubricCriterion("c1", "Engineering", 1.0),)
    first = _criteria_index(criteria)
    second = _criteria_index(criteria)
    assert first is second
    assert _criteria_index.cache_info().maxsize == 128
    assert set(first) == {"c1"}
    assert Permission.APPLICATION_READ.value == "application:read"
