from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapters.local_hybrid_index import LocalHybridIndex
from app.adapters.sqlite_repo import SQLiteRepository
from app.api.deps import get_auth_service, get_current_user, get_index, get_repo
from app.api.main import create_app
from app.domain.enums import ApplicationStage, Role
from app.domain.models import (
    Application,
    CandidateProfile,
    CandidateRecord,
    EducationEntry,
    ExperienceEntry,
    User,
)
from app.services.auth_service import AuthService
from app.services.talent_search_service import TalentSearchService


def make_candidate(
    candidate_id: str,
    tenant_id: str,
    name: str,
    skills: list[str],
    years: float,
    text: str,
) -> CandidateRecord:
    return CandidateRecord(
        id=candidate_id,
        tenant_id=tenant_id,
        file_hash=f"hash-{candidate_id}",
        filename=f"{name.split()[0]}.txt",
        storage_key=f"resumes/{tenant_id}/{candidate_id}.txt",
        profile=CandidateProfile(
            full_name=name,
            email=f"{name.split()[0].lower()}@example.com",
            phone="+1 555 123 4567",
            links=[],
            total_experience_years=years,
            skills=skills,
            experience_entries=[ExperienceEntry("Engineer", "Acme", int(years * 12), [])],
            education=[EducationEntry("State U", "BSc", "2016")],
            raw_chunks=[text],
            raw_text=text,
        ),
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )


@pytest.fixture()
def data(tmp_path: Path) -> tuple[TalentSearchService, SQLiteRepository, LocalHybridIndex, CandidateRecord, CandidateRecord, CandidateRecord]:
    repo = SQLiteRepository(tmp_path / "talentos.db")
    index = LocalHybridIndex(tmp_path / "index.json")
    alice = make_candidate(
        "alice", "org-1", "Alice Smith", ["python", "sql"], 8.0,
        "Alice Smith built Python services with SQL reporting and distributed systems.",
    )
    bob = make_candidate(
        "bob", "org-1", "Bob Jones", ["java"], 2.0,
        "Bob Jones is a Java developer who knows a bit of Python.",
    )
    carol = make_candidate(
        "carol", "org-2", "Carol Lee", ["python", "sql"], 10.0,
        "Carol Lee is a Python SQL architect with distributed services.",
    )
    for record in (alice, bob, carol):
        repo.upsert_candidate(record)
        index.upsert(
            record.id,
            record.tenant_id,
            record.profile.raw_text,
            {"skills": record.profile.skills, "full_name": record.profile.full_name},
        )
    repo.add_application(
        Application("app-a", "org-1", "alice", "job-1", ApplicationStage.SHORTLISTED, "2026-01-01T00:00:00+00:00")
    )
    repo.add_application(
        Application("app-b", "org-1", "bob", "job-1", ApplicationStage.NEW, "2026-01-01T00:00:00+00:00")
    )
    repo.add_user(User("admin", "org-1", Role.ADMIN))
    repo.add_user(User("viewer", "org-1", Role.VIEWER))
    return TalentSearchService(repo, index), repo, index, alice, bob, carol


def test_search_respects_organization_boundary(
    data: tuple[TalentSearchService, SQLiteRepository, LocalHybridIndex, CandidateRecord, CandidateRecord, CandidateRecord]
) -> None:
    service, _, _, alice, _, _ = data
    results = service.search("org-1", "distributed systems")
    assert [result.candidate_id for result in results] == [alice.id]
    assert service.search("org-2", "distributed systems")[0].candidate_id == "carol"
    assert service.search("org-1", "python") and all(
        result.candidate_id != "carol" for result in service.search("org-1", "python")
    )


def test_results_are_ranked_by_similarity(
    data: tuple[TalentSearchService, SQLiteRepository, LocalHybridIndex, CandidateRecord, CandidateRecord, CandidateRecord]
) -> None:
    service, _, _, alice, bob, _ = data
    results = service.search("org-1", "python sql distributed services")
    assert [result.candidate_id for result in results] == [alice.id, bob.id]
    assert results[0].score > results[1].score


def test_min_experience_filter(
    data: tuple[TalentSearchService, SQLiteRepository, LocalHybridIndex, CandidateRecord, CandidateRecord, CandidateRecord]
) -> None:
    service, _, _, alice, bob, _ = data
    assert [r.candidate_id for r in service.search("org-1", "python", min_experience_years=5.0)] == [alice.id]
    assert service.search("org-1", "python", min_experience_years=50.0) == []
    assert bob.id in {r.candidate_id for r in service.search("org-1", "python", min_experience_years=2.0)}


def test_required_skills_filter(
    data: tuple[TalentSearchService, SQLiteRepository, LocalHybridIndex, CandidateRecord, CandidateRecord, CandidateRecord]
) -> None:
    service, _, _, alice, _, _ = data
    assert [r.candidate_id for r in service.search("org-1", "python", required_skills=["python", "sql"])] == [alice.id]
    assert service.search("org-1", "python", required_skills=["rust"]) == []


def test_stage_filter(
    data: tuple[TalentSearchService, SQLiteRepository, LocalHybridIndex, CandidateRecord, CandidateRecord, CandidateRecord]
) -> None:
    service, _, _, alice, _, _ = data
    assert [r.candidate_id for r in service.search("org-1", "python", stage=ApplicationStage.SHORTLISTED)] == [alice.id]
    assert service.search("org-1", "python", stage=ApplicationStage.OFFER) == []


def test_excerpt_highlights_query_terms(
    data: tuple[TalentSearchService, SQLiteRepository, LocalHybridIndex, CandidateRecord, CandidateRecord, CandidateRecord]
) -> None:
    service, _, _, alice, _, _ = data
    result = next(r for r in service.search("org-1", "python") if r.candidate_id == alice.id)
    assert "<mark>python</mark>" in result.highlighted_excerpt.lower()


def test_api_search_enforces_tenant_and_rbac(
    data: tuple[TalentSearchService, SQLiteRepository, LocalHybridIndex, CandidateRecord, CandidateRecord, CandidateRecord]
) -> None:
    _, repo, index, _, _, _ = data
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: AuthService(repo)
    app.dependency_overrides[get_repo] = lambda: repo
    app.dependency_overrides[get_index] = lambda: index
    app.dependency_overrides[get_current_user] = lambda: repo.get_user("admin")
    client = TestClient(app)
    try:
        response = client.post(
            "/search/talent",
            headers={"X-Tenant-Id": "org-1"},
            json={"query": "python", "required_skills": ["sql"], "min_experience_years": 5.0},
        )
        assert response.status_code == 200
        assert [item["candidate_id"] for item in response.json()] == ["alice"]

        app.dependency_overrides[get_current_user] = lambda: repo.get_user("viewer")
        forbidden = client.post(
            "/search/talent", headers={"X-Tenant-Id": "org-1"}, json={"query": "python"}
        )
        assert forbidden.status_code == 403
    finally:
        app.dependency_overrides.clear()
