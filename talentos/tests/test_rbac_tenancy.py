from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapters.sqlite_repo import SQLiteRepository
from app.api.deps import get_auth_service, get_current_user, get_job_service
from app.api.main import create_app
from app.domain.enums import Role
from app.domain.exceptions import ForbiddenError, NotFoundError, TenantMismatchError
from app.domain.models import RubricCriterion, Tenant, User
from app.services.auth_service import AuthService
from app.services.job_service import JobService

RUBRIC = [RubricCriterion(id="c1", name="Skills", weight=1.0)]


@pytest.fixture()
def repo(tmp_path: Path) -> SQLiteRepository:
    store = SQLiteRepository(tmp_path / "talentos.db")
    store.add_tenant(Tenant(id="t1", name="Acme"))
    store.add_tenant(Tenant(id="t2", name="Globex"))
    store.add_user(User(id="admin1", tenant_id="t1", role=Role.ADMIN))
    store.add_user(User(id="viewer1", tenant_id="t1", role=Role.VIEWER))
    store.add_user(User(id="recruiter1", tenant_id="t1", role=Role.RECRUITER))
    store.add_user(User(id="admin2", tenant_id="t2", role=Role.ADMIN))
    return store


@pytest.fixture()
def services(repo: SQLiteRepository) -> tuple[AuthService, JobService]:
    auth = AuthService(repo)
    return auth, JobService(repo, auth)


def test_admin_can_create_and_read_job(services: tuple[AuthService, JobService]) -> None:
    auth, jobs = services
    admin = auth.authenticate("admin1", "t1")
    job = jobs.create_job(user=admin, tenant_id="t1", title="Engineer", rubric=RUBRIC)
    assert job.tenant_id == "t1"
    assert jobs.get_job(user=admin, tenant_id="t1", job_id=job.id).id == job.id


def test_viewer_cannot_create_job(services: tuple[AuthService, JobService]) -> None:
    auth, jobs = services
    viewer = auth.authenticate("viewer1", "t1")
    with pytest.raises(ForbiddenError):
        jobs.create_job(user=viewer, tenant_id="t1", title="Engineer", rubric=RUBRIC)


def test_recruiter_can_create_job(services: tuple[AuthService, JobService]) -> None:
    auth, jobs = services
    recruiter = auth.authenticate("recruiter1", "t1")
    job = jobs.create_job(user=recruiter, tenant_id="t1", title="Engineer", rubric=RUBRIC)
    assert job.created_by == "recruiter1"


def test_authenticate_rejects_cross_tenant_header(
    services: tuple[AuthService, JobService],
) -> None:
    auth, _ = services
    with pytest.raises(TenantMismatchError):
        auth.authenticate("admin1", "t2")


def test_job_is_not_visible_to_other_tenant(
    services: tuple[AuthService, JobService],
) -> None:
    auth, jobs = services
    admin1 = auth.authenticate("admin1", "t1")
    job = jobs.create_job(user=admin1, tenant_id="t1", title="Engineer", rubric=RUBRIC)

    admin2 = auth.authenticate("admin2", "t2")
    assert jobs.list_jobs(user=admin2, tenant_id="t2") == []
    with pytest.raises(NotFoundError):
        jobs.get_job(user=admin2, tenant_id="t2", job_id=job.id)


def test_cannot_access_another_tenant_id(
    services: tuple[AuthService, JobService],
) -> None:
    auth, jobs = services
    admin1 = auth.authenticate("admin1", "t1")
    with pytest.raises(TenantMismatchError):
        jobs.list_jobs(user=admin1, tenant_id="t2")


def test_api_header_auth_enforces_tenant(services: tuple[AuthService, JobService]) -> None:
    auth, job_service = services
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: auth
    app.dependency_overrides[get_job_service] = lambda: job_service
    client = TestClient(app)
    try:
        response = client.get("/jobs", headers={"X-User-Id": "admin1", "X-Tenant-Id": "t2"})
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_api_viewer_create_is_forbidden(services: tuple[AuthService, JobService]) -> None:
    auth, job_service = services
    viewer = auth.authenticate("viewer1", "t1")
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: viewer
    app.dependency_overrides[get_job_service] = lambda: job_service
    client = TestClient(app)
    try:
        response = client.post(
            "/jobs",
            headers={"X-Tenant-Id": "t1"},
            json={"title": "Engineer", "rubric": [{"id": "c1", "name": "Skills", "weight": 1.0}]},
        )
        assert response.status_code == 403
        assert client.get("/health").json() == {"status": "ok"}
    finally:
        app.dependency_overrides.clear()


def test_api_admin_create_returns_201(services: tuple[AuthService, JobService]) -> None:
    auth, job_service = services
    admin = auth.authenticate("admin1", "t1")
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_job_service] = lambda: job_service
    client = TestClient(app)
    try:
        response = client.post(
            "/jobs",
            headers={"X-Tenant-Id": "t1"},
            json={"title": "Engineer", "rubric": [{"id": "c1", "name": "Skills", "weight": 1.0}]},
        )
        assert response.status_code == 201
        assert response.json()["tenant_id"] == "t1"
        assert response.json()["created_by"] == "admin1"
    finally:
        app.dependency_overrides.clear()
