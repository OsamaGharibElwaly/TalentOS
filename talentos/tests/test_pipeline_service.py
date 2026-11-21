from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapters.sqlite_repo import SQLiteRepository
from app.api.deps import get_auth_service, get_current_user, get_repo
from app.api.main import create_app
from app.domain.enums import ApplicationStage, Role
from app.domain.exceptions import ForbiddenError, InvalidStageTransitionError
from app.domain.models import (
    Application,
    CandidateProfile,
    CandidateRecord,
    EducationEntry,
    ExperienceEntry,
    User,
)
from app.services.auth_service import AuthService
from app.services.pipeline_service import PipelineService


@pytest.fixture()
def repo(tmp_path: Path) -> SQLiteRepository:
    store = SQLiteRepository(tmp_path / "talentos.db")
    store.add_user(User("admin-1", "org-1", Role.ADMIN))
    store.upsert_candidate(
        CandidateRecord(
            id="cand-1",
            tenant_id="org-1",
            file_hash="hash-cand-1",
            filename="cand.txt",
            storage_key="resumes/org-1/hash-cand-1.txt",
            profile=CandidateProfile(
                full_name="Test Candidate",
                email="test@example.com",
                phone="+1 555 000 0000",
                links=[],
                total_experience_years=1.0,
                skills=[],
                experience_entries=[ExperienceEntry("Engineer", "Acme", 12, [])],
                education=[EducationEntry("State U", "BSc", "2020")],
                raw_chunks=["Test Candidate"],
            ),
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
        )
    )
    store.add_application(
        Application("app-1", "org-1", "cand-1", "job-1", ApplicationStage.NEW, "2026-01-01T00:00:00+00:00")
    )
    return store


def actor(repo: SQLiteRepository) -> User:
    user = repo.get_user("admin-1")
    assert user is not None
    return user


def service(repo: SQLiteRepository) -> PipelineService:
    return PipelineService(repo)


def test_full_transition_chain_is_audited(repo: SQLiteRepository) -> None:
    pipeline = service(repo)
    chain = [
        (ApplicationStage.SCREENED, ""),
        (ApplicationStage.SHORTLISTED, ""),
        (ApplicationStage.INTERVIEW, ""),
        (ApplicationStage.FINAL_REVIEW, ""),
        (ApplicationStage.OFFER, "approved by hiring committee"),
    ]
    for stage, reason in chain:
        result = pipeline.transition(
            tenant_id="org-1",
            application_id="app-1",
            actor=actor(repo),
            to_stage=stage,
            reason=reason,
            confirm=stage in {ApplicationStage.OFFER, ApplicationStage.REJECTED},
        )
        assert result.stage == stage

    assert repo.get_application("org-1", "app-1").stage == ApplicationStage.OFFER
    logs = repo.list_audit_logs("org-1", "app-1")
    assert len(logs) == len(chain)
    assert [log.to_stage for log in logs] == [stage for stage, _ in chain]
    assert {log.actor_id for log in logs} == {"admin-1"}
    assert logs[-1].reason == "approved by hiring committee"


def test_invalid_transition_is_rejected(repo: SQLiteRepository) -> None:
    with pytest.raises(InvalidStageTransitionError):
        service(repo).transition(
            tenant_id="org-1",
            application_id="app-1",
            actor=actor(repo),
            to_stage=ApplicationStage.INTERVIEW,
        )
    assert repo.list_audit_logs("org-1", "app-1") == []


def test_offer_requires_explicit_confirmation_and_reason(repo: SQLiteRepository) -> None:
    pipeline = service(repo)
    for stage in [
        ApplicationStage.SCREENED,
        ApplicationStage.SHORTLISTED,
        ApplicationStage.INTERVIEW,
        ApplicationStage.FINAL_REVIEW,
    ]:
        pipeline.transition(
            tenant_id="org-1", application_id="app-1", actor=actor(repo), to_stage=stage
        )
    with pytest.raises(ForbiddenError):
        pipeline.transition(
            tenant_id="org-1", application_id="app-1", actor=actor(repo), to_stage=ApplicationStage.OFFER
        )
    with pytest.raises(ForbiddenError):
        pipeline.transition(
            tenant_id="org-1", application_id="app-1", actor=actor(repo),
            to_stage=ApplicationStage.OFFER, confirm=True, reason="  ",
        )
    assert repo.get_application("org-1", "app-1").stage == ApplicationStage.FINAL_REVIEW


def test_ai_recommendation_never_changes_state(repo: SQLiteRepository) -> None:
    recommendation = service(repo).recommend(
        tenant_id="org-1",
        application_id="app-1",
        to_stage=ApplicationStage.OFFER,
        rationale="strong rubric scores",
    )
    assert recommendation.requires_human_confirmation is True
    assert recommendation.from_stage == ApplicationStage.NEW
    assert repo.get_application("org-1", "app-1").stage == ApplicationStage.NEW
    assert repo.list_audit_logs("org-1", "app-1") == []


def test_rejection_is_allowed_from_new_and_is_terminal(repo: SQLiteRepository) -> None:
    pipeline = service(repo)
    pipeline.transition(
        tenant_id="org-1", application_id="app-1", actor=actor(repo),
        to_stage=ApplicationStage.REJECTED, confirm=True, reason="failed mandatory criterion",
    )
    with pytest.raises(InvalidStageTransitionError):
        pipeline.transition(
            tenant_id="org-1", application_id="app-1", actor=actor(repo),
            to_stage=ApplicationStage.SCREENED,
        )


def test_api_transition_endpoint_requires_confirmation(repo: SQLiteRepository) -> None:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: AuthService(repo)
    app.dependency_overrides[get_repo] = lambda: repo
    app.dependency_overrides[get_current_user] = lambda: repo.get_user("admin-1")
    client = TestClient(app)
    headers = {"X-Tenant-Id": "org-1"}
    try:
        unconfirmed = client.post(
            "/applications/app-1/transition",
            headers=headers,
            json={"to_stage": "REJECTED", "reason": "not a fit"},
        )
        assert unconfirmed.status_code == 403
        confirmed = client.post(
            "/applications/app-1/transition",
            headers=headers,
            json={"to_stage": "REJECTED", "reason": "not a fit", "confirm": True},
        )
        assert confirmed.status_code == 200
        assert confirmed.json()["stage"] == "REJECTED"
        assert len(repo.list_audit_logs("org-1", "app-1")) == 1
    finally:
        app.dependency_overrides.clear()
