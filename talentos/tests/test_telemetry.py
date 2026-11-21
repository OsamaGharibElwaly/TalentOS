from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapters.sqlite_repo import SQLiteRepository
from app.api.deps import get_auth_service, get_current_user, get_repo
from app.api.main import create_app
from app.domain.enums import Role
from app.domain.models import User
from app.services.auth_service import AuthService
from app.services.telemetry_service import TelemetryService


@pytest.fixture()
def repo(tmp_path: Path) -> SQLiteRepository:
    store = SQLiteRepository(tmp_path / "talentos.db")
    store.add_user(User("admin", "org-1", Role.ADMIN))
    store.add_user(User("viewer", "org-1", Role.VIEWER))
    return store


def test_track_persists_bounded_metrics(repo: SQLiteRepository) -> None:
    service = TelemetryService(repo)
    event = service.track(
        tenant_id="org-1",
        operation="score_resume",
        provider="offline",
        model="offline-extractor",
        latency_ms=12.5,
        tokens_in=100,
        tokens_out=20,
        citation_pass_rate=2.5,
        status="ok",
    )
    assert event.citation_pass_rate == 1.0
    assert event.latency_ms == 12.5
    stored = repo.list_telemetry("org-1")
    assert len(stored) == 1
    assert stored[0].id == event.id
    assert stored[0].provider == "offline"


def test_summary_aggregates_and_is_tenant_scoped(repo: SQLiteRepository) -> None:
    service = TelemetryService(repo)
    service.track(
        tenant_id="org-1", operation="score", latency_ms=10.0,
        tokens_in=5, tokens_out=2, citation_pass_rate=0.5,
    )
    service.track(
        tenant_id="org-1", operation="score", latency_ms=20.0,
        tokens_in=5, tokens_out=4, citation_pass_rate=1.0, status="error",
    )
    service.track(tenant_id="org-2", operation="score", latency_ms=100.0)

    summary = service.summary("org-1")
    assert summary.total_operations == 2
    assert summary.success_count == 1
    assert summary.failure_count == 1
    assert summary.average_latency_ms == 15.0
    assert summary.tokens_in == 10
    assert summary.tokens_out == 6
    assert summary.citation_pass_rate == pytest.approx(0.75)
    assert summary.by_operation == {"score": 2}
    assert service.summary("org-2").total_operations == 1


def test_empty_summary_is_zeroed(repo: SQLiteRepository) -> None:
    summary = TelemetryService(repo).summary("org-1")
    assert summary.total_operations == 0
    assert summary.average_latency_ms == 0.0
    assert summary.by_operation == {}


def test_summary_endpoint_is_admin_only(repo: SQLiteRepository) -> None:
    TelemetryService(repo).track(tenant_id="org-1", operation="score", latency_ms=1.0)
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: AuthService(repo)
    app.dependency_overrides[get_repo] = lambda: repo
    app.dependency_overrides[get_current_user] = lambda: repo.get_user("admin")
    client = TestClient(app)
    try:
        allowed = client.get("/api/v1/telemetry/summary", headers={"X-Tenant-Id": "org-1"})
        assert allowed.status_code == 200
        assert allowed.json()["total_operations"] == 1

        app.dependency_overrides[get_current_user] = lambda: repo.get_user("viewer")
        denied = client.get("/api/v1/telemetry/summary", headers={"X-Tenant-Id": "org-1"})
        assert denied.status_code == 403
    finally:
        app.dependency_overrides.clear()
