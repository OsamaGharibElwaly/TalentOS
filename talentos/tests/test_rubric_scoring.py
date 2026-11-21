from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapters.sqlite_repo import SQLiteRepository
from app.api.deps import get_auth_service, get_current_user, get_repo
from app.api.main import create_app
from app.domain.enums import ApplicationStage, Role
from app.domain.models import (
    Application,
    CandidateProfile,
    CandidateRecord,
    CriterionEvaluation,
    EducationEntry,
    ExperienceEntry,
    Job,
    RubricCriterion,
    User,
)
from app.services.auth_service import AuthService
from app.services.citation_verifier import CitationVerifier
from app.services.pii_redactor import PIIRedactor
from app.services.scoring_service import ScoringService

RAW = """Jane Doe
jane.doe@example.com | +1 555 123 4567
https://linkedin.com/in/jane
EXPERIENCE
Built Python services at Acme Corp
Collaborated with designers and SQL analysts
EDUCATION
BSc Computer Science, State University, 2016
SKILLS
Python, SQL, Docker
"""


@pytest.fixture()
def repo(tmp_path: Path) -> SQLiteRepository:
    store = SQLiteRepository(tmp_path / "talentos.db")
    store.add_user(User("admin", "org-1", Role.ADMIN))
    store.add_user(User("hm", "org-1", Role.HIRING_MANAGER))
    return store


@pytest.fixture()
def candidate() -> CandidateProfile:
    return CandidateProfile(
        full_name="Jane Doe",
        email="jane.doe@example.com",
        phone="+1 555 123 4567",
        links=["https://linkedin.com/in/jane"],
        total_experience_years=5.0,
        skills=["python", "sql", "docker"],
        experience_entries=[ExperienceEntry("Engineer", "Acme", 60, [])],
        education=[EducationEntry("State University", "BSc", "2016")],
        raw_chunks=["Jane Doe", "EXPERIENCE"],
        raw_text=RAW,
    )


@pytest.fixture()
def job() -> Job:
    return Job(
        id="job1",
        tenant_id="org-1",
        title="Engineer",
        rubric=[
            RubricCriterion("c1", "Engineering", 0.6, mandatory=True),
            RubricCriterion("c2", "Collaboration", 0.4),
        ],
        created_by="admin",
    )


@pytest.fixture()
def application() -> Application:
    return Application(
        id="app1",
        tenant_id="org-1",
        candidate_id="cand1",
        job_id="job1",
        stage=ApplicationStage.NEW,
        created_at="2026-01-01T00:00:00+00:00",
    )


@pytest.fixture()
def service(repo: SQLiteRepository) -> ScoringService:
    return ScoringService(CitationVerifier(), PIIRedactor(), repo)


def test_weighted_composite_matches_manual_math(
    service: ScoringService,
    candidate: CandidateProfile,
    job: Job,
    application: Application,
) -> None:
    result = service.score(
        application=application,
        candidate=candidate,
        job=job,
        evaluations=[
            CriterionEvaluation("c1", 80, "Strong Python", ["Built Python services"], 1.0),
            CriterionEvaluation("c2", 90, "Good teamwork", ["Collaborated with designers"], 1.0),
        ],
    )
    assert result.composite_score == pytest.approx(80 * 0.6 / 100 + 90 * 0.4 / 100, abs=1e-4)
    assert result.composite_score == pytest.approx(0.84, abs=1e-4)


def test_fabricated_justification_is_never_persisted(
    service: ScoringService,
    repo: SQLiteRepository,
    candidate: CandidateProfile,
    job: Job,
    application: Application,
) -> None:
    result = service.score(
        application=application,
        candidate=candidate,
        job=job,
        evaluations=[
            CriterionEvaluation("c1", 95, "Led a team of 50", ["led a team of 50 engineers"], 1.0)
        ],
    )
    scored = result.criterion_scores[0]
    assert scored.rationale == ""
    assert scored.citations == []
    assert scored.confidence == pytest.approx(0.25)

    stored = repo.get_scoring_result(application.id)
    assert stored is not None
    assert stored.criterion_scores[0].rationale == ""
    assert stored.criterion_scores[0].citations == []


def test_gaps_flag_missing_mandatory_evidence_and_unsubstantiated_skills(
    service: ScoringService,
    candidate: CandidateProfile,
    job: Job,
    application: Application,
) -> None:
    result = service.score(
        application=application,
        candidate=candidate,
        job=job,
        evaluations=[CriterionEvaluation("c1", 80, "Unsupported", ["totally invented"])],
    )
    gaps = {(gap.kind, gap.criterion_id) for gap in result.gaps_and_probes}
    assert ("missing_mandatory_criterion", "c1") in gaps
    assert ("unsubstantiated_skill", "c1") in gaps
    assert ("unsubstantiated_skill", "profile") in gaps


def test_blind_mode_strips_pii_before_scoring_input(
    service: ScoringService,
    candidate: CandidateProfile,
    job: Job,
    application: Application,
) -> None:
    result = service.score(
        application=application,
        candidate=candidate,
        job=job,
        evaluations=[CriterionEvaluation("c1", 90, "Contactable", ["jane.doe@example.com"])],
        blind_mode=True,
    )
    assert result.blind_mode is True
    assert result.criterion_scores[0].citations == []
    assert result.criterion_scores[0].rationale == ""


def test_redactor_removes_all_pii_token_types(candidate: CandidateProfile) -> None:
    redacted = PIIRedactor().redact(RAW, blind_mode=True, full_name=candidate.full_name)
    for token in [
        "jane.doe@example.com",
        "+1 555 123 4567",
        "linkedin.com",
        "Jane Doe",
        "2016",
    ]:
        assert token not in redacted.text
    assert any("example.com" in token for token in redacted.stripped_tokens)


def test_hiring_manager_pii_is_masked_until_shortlisted(
    repo: SQLiteRepository, candidate: CandidateProfile
) -> None:
    repo.upsert_candidate(
        CandidateRecord(
            id="cand1",
            tenant_id="org-1",
            file_hash="hash-1",
            filename="cv.txt",
            storage_key="resumes/org-1/hash-1.txt",
            profile=candidate,
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
        )
    )
    auth = AuthService(repo)
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: auth
    app.dependency_overrides[get_repo] = lambda: repo
    app.dependency_overrides[get_current_user] = lambda: repo.get_user("admin")
    client = TestClient(app)
    headers = {"X-Tenant-Id": "org-1"}
    try:
        created = client.post(
            "/applications", headers=headers, json={"candidate_id": "cand1", "job_id": "job1"}
        )
        assert created.status_code == 201
        application_id = created.json()["id"]

        repo.add_application(
            Application(
                id="app-shortlisted",
                tenant_id="org-1",
                candidate_id="cand1",
                job_id="job1",
                stage=ApplicationStage.SHORTLISTED,
                created_at="2026-01-01T00:00:00+00:00",
            )
        )

        app.dependency_overrides[get_current_user] = lambda: repo.get_user("hm")
        masked = client.get(f"/applications/{application_id}", headers=headers)
        assert masked.status_code == 200
        assert masked.json()["email"] != candidate.email
        assert "*" in masked.json()["phone"]

        visible = client.get("/applications/app-shortlisted", headers=headers)
        assert visible.status_code == 200
        assert visible.json()["email"] == candidate.email
        assert visible.json()["phone"] == candidate.phone
    finally:
        app.dependency_overrides.clear()
