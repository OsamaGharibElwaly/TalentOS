from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from app.adapters.local_hybrid_index import LocalHybridIndex
from app.adapters.local_storage import LocalStorage
from app.adapters.sqlite_repo import SQLiteRepository
from app.api import routes_frontend
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
from app.domain.exceptions import ForbiddenError
from app.domain.models import (
    Application,
    CandidateProfile,
    CandidateRecord,
    Job,
    RubricCriterion,
    User,
)
from app.services.auth_service import AuthService

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
SRC = FRONTEND / "src"

REQUIRED_FILES = (
    "next.config.ts",
    "tsconfig.json",
    "package.json",
    "src/app/layout.tsx",
    "src/app/loading.tsx",
    "src/app/error.tsx",
    "src/app/global-error.tsx",
    "src/app/not-found.tsx",
    "src/app/page.tsx",
    "src/app/guide/page.tsx",
    "src/app/login/page.tsx",
    "src/app/globals.css",
    "src/app/jobs/page.tsx",
    "src/app/ingestion/page.tsx",
    "src/app/candidates/page.tsx",
    "src/app/interviews/page.tsx",
    "src/app/talent-pool/page.tsx",
    "src/app/telemetry/page.tsx",
    "src/components/shell/AppShell.tsx",
    "src/components/shell/SidebarNav.tsx",
    "src/components/shell/WorkspaceRbacBar.tsx",
    "src/components/jobs/RubricWeightEditor.tsx",
    "src/components/ingestion/BulkResumeDropzone.tsx",
    "src/components/candidates/SplitEvidenceViewer.tsx",
    "src/components/interviews/InterviewCopilotPanel.tsx",
    "src/components/search/TalentSearchWorkbench.tsx",
    "src/components/telemetry/TelemetryMetricsGrid.tsx",
    "src/components/telemetry/InsightsPanel.tsx",
    "src/components/dashboard/HiringDashboard.tsx",
    "src/components/ui/Icon.tsx",
    "src/components/ui/BrandMark.tsx",
    "src/components/ui/LoadingScreen.tsx",
    "src/components/ui/Skeletons.tsx",
    "src/components/ui/ErrorState.tsx",
    "src/components/ui/DeveloperMode.tsx",
    "src/lib/developer-recipes.ts",
    "src/lib/loading.ts",
    "src/lib/navigation.ts",
    "src/lib/api-client.ts",
    "src/lib/auth-session.ts",
    "src/lib/errors.ts",
    "src/lib/security.ts",
    "src/types/talentos.ts",
)

RESUME = b"""Alice Rivera
alice.rivera@example.com
8 years of experience delivering backend systems.

SKILLS
python, sql, fastapi

EXPERIENCE
Senior Engineer | Acme | 36 months
- Built services with Python
"""


def _source(path: str) -> str:
    return (SRC / path).read_text(encoding="utf-8")


def _ts_array(text: str, name: str) -> list[str]:
    match = re.search(rf"export const {name}[^=]*=\s*\[(.*?)\];", text, re.S)
    assert match is not None, f"{name} is missing"
    return re.findall(r"'([^']+)'", match.group(1))


def _denies(auth: AuthService, user: User, permission: Permission) -> bool:
    try:
        auth.require(user, permission)
    except ForbiddenError:
        return True
    return False


def _profile() -> CandidateProfile:
    return CandidateProfile(
        full_name="Alice Rivera",
        email="alice.rivera@example.com",
        phone="+15551234567",
        links=[],
        total_experience_years=8,
        skills=["python"],
        experience_entries=[],
        education=[],
        raw_chunks=[],
        raw_text="Built services with Python",
    )


@pytest.fixture()
def harness(tmp_path: Path) -> Iterator[tuple[SQLiteRepository, TestClient]]:
    repo = SQLiteRepository(tmp_path / "talentos.db")
    for user_id, role in (
        ("admin", Role.ADMIN),
        ("recruiter", Role.RECRUITER),
        ("manager", Role.HIRING_MANAGER),
        ("viewer", Role.VIEWER),
    ):
        repo.add_user(User(user_id, "org-1", role))
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
    return {"X-User-Id": user_id, "X-Tenant-Id": "org-1"}


def test_required_nextjs_files_exist_and_are_non_empty() -> None:
    for relative in REQUIRED_FILES:
        path = FRONTEND / relative
        assert path.is_file(), relative
        assert path.stat().st_size > 0, relative


def test_typescript_is_strict_and_uses_no_any() -> None:
    config = json.loads((FRONTEND / "tsconfig.json").read_text(encoding="utf-8"))
    assert config["compilerOptions"]["strict"] is True
    for path in SRC.rglob("*"):
        if path.suffix in {".ts", ".tsx"}:
            assert re.search(r"\bany\b", path.read_text(encoding="utf-8")) is None, path


def test_api_client_paths_exist_on_backend() -> None:
    client_text = _source("lib/api-client.ts")
    for path in (
        "/frontend/session",
        "/frontend/candidates",
        "/frontend/account",
        "/frontend/insights",
        "/frontend/scoring",
        "/frontend/ingest",
        "/jobs",
        "/interviews/questions",
        "/interviews/scorecards",
        "/search/talent",
        "/api/v1/telemetry/summary",
        "/transition",
    ):
        assert path in client_text, path
    schema_paths = set(create_app().openapi()["paths"])
    for path in (
        "/frontend/session",
        "/frontend/candidates",
        "/frontend/account",
        "/frontend/insights",
        "/frontend/scoring",
        "/frontend/ingest",
        "/jobs",
        "/interviews/questions",
        "/interviews/scorecards",
        "/search/talent",
        "/api/v1/telemetry/summary",
        "/applications/{application_id}/transition",
    ):
        assert path in schema_paths, path


def test_ui_uses_vector_icons_and_has_sign_in() -> None:
    emoji = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
    for relative in (
        "app/page.tsx",
        "app/guide/page.tsx",
        "components/dashboard/HiringDashboard.tsx",
        "components/shell/SidebarNav.tsx",
    ):
        assert emoji.search(_source(relative)) is None, relative
    icons = _source("components/ui/Icon.tsx")
    for name in ("briefcase", "users", "chat", "trophy", "chart", "clipboard", "lock", "shield"):
        assert f"  {name}:" in icons, name
    login = _source("app/login/page.tsx")
    for token in ("writeSession", "createAccount", "org-1", "admin", "recruiter", "Work email"):
        assert token in login, token
    not_found = _source("app/not-found.tsx")
    for token in ("BrandMark", "ErrorState", "could not find that page"):
        assert token in not_found, token
    permission_bar = _source("components/shell/WorkspaceRbacBar.tsx")
    for token in ("permissionIcon", "permissionTone", "roleIcon", "roleTone"):
        assert token in permission_bar, token
    score_view = _source("components/candidates/SplitEvidenceViewer.tsx")
    assert "* 100" in score_view and "%" in score_view
    assert "src/app/loading.tsx" in REQUIRED_FILES
    assert "src/app/error.tsx" in REQUIRED_FILES
    assert "src/app/not-found.tsx" in REQUIRED_FILES


def test_every_feature_page_has_guided_json_developer_mode() -> None:
    recipe_text = _source("lib/developer-recipes.ts")
    for key in (
        "overview", "guide", "jobs", "ingestion", "candidates",
        "interviews", "talentPool", "telemetry", "login",
    ):
        assert f"  {key}: {{" in recipe_text, key
    for page in (
        "app/page.tsx",
        "app/guide/page.tsx",
        "app/jobs/page.tsx",
        "app/ingestion/page.tsx",
        "app/candidates/page.tsx",
        "app/interviews/page.tsx",
        "app/talent-pool/page.tsx",
        "app/telemetry/page.tsx",
        "app/login/page.tsx",
    ):
        text = _source(page)
        assert "DeveloperMode" in text and "DEVELOPER_RECIPES" in text, page
    component = _source("components/ui/DeveloperMode.tsx")
    assert "JSON.stringify({ process, steps }, null, 2)" in component
    styles = _source("app/globals.css")
    assert ".developer-mode pre" in styles


def test_loading_states_are_visible_and_motion_is_optional() -> None:
    loader = _source("components/ui/LoadingScreen.tsx")
    assert "PageSkeleton" in loader
    assert "spinner-orbit" in loader
    assert "withMinimumDelay" in _source("lib/loading.ts")
    styles = _source("app/globals.css")
    assert ".page-transition" in styles
    assert "prefers-reduced-motion" in styles


def test_api_client_payloads_use_backend_field_names() -> None:
    client_text = _source("lib/api-client.ts")
    for field in (
        "application_id",
        "candidate_id",
        "job_id",
        "evaluations",
        "blind_mode",
        "criterion_id",
        "citations",
        "confidence",
        "raw_notes",
        "min_experience_years",
        "required_skills",
        "top_k",
        "to_stage",
        "reason",
        "confirm",
    ):
        assert field in client_text, field
    session = _source("lib/auth-session.ts")
    assert "'X-User-Id'" in session
    assert "'X-Tenant-Id'" in session


def test_security_helpers_match_backend_rules() -> None:
    text = _source("lib/security.ts")
    for helper in (
        "can",
        "isPiiMasked",
        "maskEmail",
        "maskPhone",
        "isAllowedResume",
        "weightsAreValid",
        "escapeHtml",
        "renderHighlighted",
    ):
        assert f"export function {helper}(" in text, helper

    assert set(_ts_array(text, "MASKED_STAGES")) == {
        stage.value for stage in routes_frontend.MASKED_STAGES
    }
    assert set(_ts_array(text, "ALLOWED_RESUME_EXTENSIONS")) == {
        ".pdf", ".docx", ".txt", ".md"
    }

    parsed = {
        role: set(re.findall(r"'([^']+)'", body))
        for role, body in re.findall(r"^\s*(\w+): \[([^\]]*)\]", text, re.M)
    }
    assert set(parsed) == {role.value for role in Role}
    auth = AuthService(None)  # type: ignore[arg-type]
    for role in Role:
        expected = {
            permission.value
            for permission in Permission
            if not _denies(auth, User("u", "org-1", role), permission)
        }
        assert parsed[role.value] == expected, role


def test_pages_wire_every_capability_component() -> None:
    wiring = {
        "app/jobs/page.tsx": "RubricWeightEditor",
        "app/ingestion/page.tsx": "BulkResumeDropzone",
        "app/candidates/page.tsx": "SplitEvidenceViewer",
        "app/interviews/page.tsx": "InterviewCopilotPanel",
        "app/talent-pool/page.tsx": "TalentSearchWorkbench",
        "app/telemetry/page.tsx": "TelemetryMetricsGrid",
    }
    for page, component in wiring.items():
        assert component in _source(page), page
    assert "canViewRoute" in _source("components/shell/SidebarNav.tsx")
    assert "isPiiMasked" in _source("lib/auth-session.ts") or "can(" in _source("lib/auth-session.ts")
    assert "confirm" in _source("components/candidates/SplitEvidenceViewer.tsx")
    assert "canViewTelemetry" in _source("components/telemetry/TelemetryMetricsGrid.tsx")


def test_hr_friendly_navigation_and_guide_are_wired() -> None:
    nav = _source("lib/navigation.ts")
    for label in (
        "Getting Started",
        "Jobs & Scorecards",
        "Add Resumes",
        "Review Candidates",
        "Interviews",
        "Find Talent",
        "Activity & Insights",
    ):
        assert label in nav, label
    for source in ("components/shell/SidebarNav.tsx", "components/ui/CommandPalette.tsx"):
        assert "NAV_ITEMS" in _source(source), source
    assert "WORKFLOW_ITEMS" in _source("app/page.tsx")
    guide = _source("app/guide/page.tsx")
    for token in ("journey", "What you do", "Why it helps", 'href="/jobs"'):
        assert token in guide, token
    session = _source("lib/auth-session.ts")
    assert "DEFAULT_USER_ID = 'recruiter'" in session
    assert "DEFAULT_TENANT_ID = 'org-1'" in session


def test_insights_endpoint_uses_demo_data_and_respects_rbac(
    harness: tuple[SQLiteRepository, TestClient],
) -> None:
    from scripts.seed_demo import seed

    repo, client = harness
    counts = seed(repo, tenant_id="org-1")
    assert counts == {"jobs": 3, "candidates": 9, "applications": 9, "scores": 9, "events": 12}

    response = client.get("/frontend/insights", headers=_headers("recruiter"))
    assert response.status_code == 200
    body = response.json()
    assert body["applications"] == 9
    assert sum(body["by_stage"].values()) == 9
    assert body["average_score"] > 0
    assert body["top_skills"] and body["decisions"]
    assert client.get("/frontend/insights", headers=_headers("viewer")).status_code == 403

    assert seed(repo, tenant_id="org-1") == {
        "jobs": 0, "candidates": 0, "applications": 0, "scores": 0, "events": 0,
    }


def test_session_endpoint_returns_backend_permissions(harness: tuple[SQLiteRepository, TestClient]) -> None:
    _, client = harness
    admin = client.get("/frontend/session", headers=_headers("admin")).json()
    assert set(admin["permissions"]) == {permission.value for permission in Permission}
    manager = client.get("/frontend/session", headers=_headers("manager")).json()
    assert set(manager["permissions"]) == {"job:read", "application:read"}
    assert manager["tenant_id"] == "org-1"


def test_account_endpoint_creates_local_workspace_safely(
    harness: tuple[SQLiteRepository, TestClient],
) -> None:
    repo, client = harness
    payload = {
        "organization": "Northstar Hiring",
        "full_name": "Alex Morgan",
        "email": "alex@northstar.example",
    }
    response = client.post("/frontend/account", json=payload)
    assert response.status_code == 201
    account = response.json()
    assert account["role"] == "recruiter"
    assert account["organization"] == payload["organization"]
    assert repo.get_tenant(account["tenant_id"]) is not None
    assert repo.get_user(account["user_id"]) is not None

    session = client.get(
        "/frontend/session",
        headers={"X-User-Id": account["user_id"], "X-Tenant-Id": account["tenant_id"]},
    )
    assert session.status_code == 200
    assert session.json()["role"] == "recruiter"

    repeat = client.post("/frontend/account", json=payload)
    assert repeat.status_code == 201
    assert repeat.json()["user_id"] == account["user_id"]
    renamed = client.post("/frontend/account", json={**payload, "full_name": "Alex M."})
    assert renamed.status_code == 201
    assert renamed.json()["user_id"] == account["user_id"]
    assert client.post("/frontend/account", json={**payload, "email": "not-an-email"}).status_code == 422
    privileged = client.post(
        "/frontend/account",
        json={**payload, "email": "second@northstar.example", "role": "admin"},
    )
    assert privileged.status_code == 201
    assert privileged.json()["role"] == "recruiter"


def test_candidate_review_masks_pii_exactly_like_backend(harness: tuple[SQLiteRepository, TestClient]) -> None:
    repo, client = harness
    record = CandidateRecord(
        id="c1",
        tenant_id="org-1",
        file_hash="hash",
        filename="resume.txt",
        storage_key="key",
        profile=_profile(),
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )
    repo.upsert_candidate(record)
    repo.add_application(
        Application("a1", "org-1", "c1", "j1", ApplicationStage.NEW, "2026-01-01T00:00:00+00:00")
    )

    manager = client.get("/frontend/candidates", headers=_headers("manager")).json()[0]
    assert manager["pii_masked"] is True
    assert manager["email"] == "a***@example.com"
    assert manager["phone"] == "*" * len("+15551234567")

    recruiter = client.get("/frontend/candidates", headers=_headers("recruiter")).json()[0]
    assert recruiter["pii_masked"] is False
    assert recruiter["email"] == "alice.rivera@example.com"

    repo.update_application_stage("org-1", "a1", ApplicationStage.SHORTLISTED)
    revealed = client.get("/frontend/candidates", headers=_headers("manager")).json()[0]
    assert revealed["pii_masked"] is False
    assert revealed["email"] == "alice.rivera@example.com"


def test_ingest_endpoint_reports_status_duplicates_and_rbac(harness: tuple[SQLiteRepository, TestClient]) -> None:
    _, client = harness
    files = [
        ("files", ("resume.txt", RESUME, "text/plain")),
        ("files", ("malware.exe", b"MZ", "application/octet-stream")),
    ]
    response = client.post("/frontend/ingest", files=files, headers=_headers("recruiter"))
    assert response.status_code == 201
    by_name = {item["filename"]: item for item in response.json()}
    assert by_name["resume.txt"]["status"] == "INDEXED"
    assert by_name["resume.txt"]["duplicate"] is False
    assert by_name["malware.exe"]["status"] == "FAILED"
    assert by_name["malware.exe"]["error"] == "unsupported file type"

    again = client.post(
        "/frontend/ingest",
        files=[("files", ("resume.txt", RESUME, "text/plain"))],
        headers=_headers("recruiter"),
    )
    assert again.json()[0]["duplicate"] is True
    denied = client.post(
        "/frontend/ingest",
        files=[("files", ("resume.txt", RESUME, "text/plain"))],
        headers=_headers("viewer"),
    )
    assert denied.status_code == 403


def test_scoring_endpoint_returns_verified_citations(harness: tuple[SQLiteRepository, TestClient]) -> None:
    repo, client = harness
    repo.add_job(
        Job(
            id="j1",
            tenant_id="org-1",
            title="Engineer",
            rubric=[RubricCriterion("c1", "Engineering", 1.0, "Builds software", True)],
            created_by="admin",
        )
    )
    repo.upsert_candidate(
        CandidateRecord(
            id="c1",
            tenant_id="org-1",
            file_hash="hash",
            filename="resume.txt",
            storage_key="key",
            profile=_profile(),
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
        )
    )
    repo.add_application(
        Application("a1", "org-1", "c1", "j1", ApplicationStage.NEW, "2026-01-01T00:00:00+00:00")
    )
    response = client.post(
        "/frontend/scoring",
        json={
            "application_id": "a1",
            "evaluations": [
                {
                    "criterion_id": "c1",
                    "score": 90,
                    "rationale": "direct evidence",
                    "citations": ["Built services with Python"],
                    "confidence": 1.0,
                }
            ],
            "blind_mode": False,
        },
        headers=_headers("recruiter"),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["composite_score"] == pytest.approx(0.9)
    assert body["criterion_scores"][0]["citations"][0]["verified"] is True
