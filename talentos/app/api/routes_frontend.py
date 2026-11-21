from __future__ import annotations

import hashlib
import re
from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.adapters.local_hybrid_index import LocalHybridIndex
from app.adapters.local_queue import LocalAsyncQueue
from app.adapters.offline_extractor import OfflineExtractor
from app.adapters.sqlite_repo import SQLiteRepository
from app.api.deps import (
    get_auth_service,
    get_current_user,
    get_index,
    get_repo,
    get_settings,
    get_storage,
)
from app.config import Settings
from app.domain.enums import ApplicationStage, IngestionStatus, Permission, Role
from app.domain.exceptions import ForbiddenError, QueueLimitError
from app.domain.models import (
    Application,
    CriterionEvaluation,
    DocumentUpload,
    ScoringResult,
    Tenant,
    User,
)
from app.ports.storage import StoragePort
from app.services.auth_service import AuthService
from app.services.citation_verifier import CitationVerifier
from app.services.document_parser import DocumentParser
from app.services.ingestion_service import IngestionService
from app.services.insights_service import InsightsService
from app.services.pii_redactor import PIIRedactor
from app.services.scoring_service import ScoringService

router = APIRouter(prefix="/frontend", tags=["frontend"])
MASKED_STAGES = {ApplicationStage.NEW, ApplicationStage.SCREENED, ApplicationStage.REJECTED}
ALLOWED_SUFFIXES = {".pdf", ".docx", ".txt", ".md"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAGIC_BYTES: dict[str, bytes | None] = {
    ".pdf": b"%PDF-",
    ".docx": b"PK\x03\x04",
    ".txt": None,
    ".md": None,
}


def _validate_upload(filename: str, raw: bytes) -> str:
    if "/" in filename or "\\" in filename or Path(filename).name != filename:
        return "invalid filename"
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        return "unsupported file type"
    if not raw:
        return "empty file"
    if len(raw) > MAX_UPLOAD_BYTES:
        return "file too large"
    magic = MAGIC_BYTES[suffix]
    if magic is not None:
        return "" if raw.startswith(magic) else "file content does not match extension"
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return "file content is not valid text"
    return ""


class SessionOut(BaseModel):
    user_id: str
    tenant_id: str
    role: Role
    permissions: list[str]


class AccountCreateIn(BaseModel):
    organization: str = Field(min_length=2, max_length=80)
    full_name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=160)


class AccountOut(BaseModel):
    user_id: str
    tenant_id: str
    role: Role
    organization: str
    full_name: str


class UploadStatusOut(BaseModel):
    filename: str
    file_hash: str
    status: IngestionStatus
    duplicate: bool
    candidate_id: str | None = None
    error: str = ""


class EvaluationIn(BaseModel):
    criterion_id: str
    score: int
    rationale: str = ""
    citations: list[str] = Field(default_factory=list)
    confidence: float = 1.0


class ScoreRequest(BaseModel):
    application_id: str
    evaluations: list[EvaluationIn]
    blind_mode: bool = False


class ScoringResultOut(BaseModel):
    application_id: str
    candidate_id: str
    composite_score: float
    criterion_scores: list[dict[str, object]]
    gaps_and_probes: list[dict[str, str]]
    blind_mode: bool


class RankOut(BaseModel):
    label: str
    value: float


class DecisionOut(BaseModel):
    title: str
    detail: str
    href: str
    tone: str


class InsightsOut(BaseModel):
    tenant_id: str
    candidates: int
    applications: int
    by_stage: dict[str, int]
    average_score: float
    scored_applications: int
    top_skills: list[RankOut]
    ready_to_interview: list[RankOut]
    needs_review: int
    decisions: list[DecisionOut]


class ApplicationSummaryOut(BaseModel):
    id: str
    job_id: str
    stage: ApplicationStage
    scoring: ScoringResultOut | None = None


class CandidateReviewOut(BaseModel):
    candidate_id: str
    full_name: str
    email: str
    phone: str
    skills: list[str]
    total_experience_years: float
    raw_text: str
    pii_masked: bool
    applications: list[ApplicationSummaryOut]


def _require(auth: AuthService, user: User, permission: Permission) -> None:
    try:
        auth.require(user, permission)
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _scoring_out(result: ScoringResult) -> ScoringResultOut:
    return ScoringResultOut(**asdict(result))


def _mask_email(value: str) -> str:
    local, separator, domain = value.partition("@")
    return f"{local[:1]}***@{domain}" if separator else "***"


def _masked(role: Role, stages: set[ApplicationStage]) -> bool:
    return role == Role.HIRING_MANAGER and not any(
        stage not in MASKED_STAGES for stage in stages
    )


_ACCOUNT_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:24] or "workspace"


def _id_for(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()[:8]


@router.post("/account", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreateIn,
    repo: SQLiteRepository = Depends(get_repo),
) -> AccountOut:
    """Create (or re-open) a local workspace for a new HR user."""
    organization = payload.organization.strip()
    full_name = payload.full_name.strip()
    email = payload.email.strip().lower()
    if len(organization) < 2 or len(full_name) < 2 or not _ACCOUNT_EMAIL.match(email):
        raise HTTPException(
            status_code=422,
            detail="Enter an organization, your name and a valid work email.",
        )

    tenant_id = f"{_slug(organization)}-{_id_for(organization)}"
    user_id = f"user-{_id_for(organization + '|' + email)}"
    user = repo.get_user(user_id)
    if user is not None and user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=409,
            detail="This work email is already registered in another workspace.",
        )
    if repo.get_tenant(tenant_id) is None:
        repo.add_tenant(Tenant(tenant_id, organization))
    if user is None:
        # Self-registration never grants admin or telemetry access.
        user = User(user_id, tenant_id, Role.RECRUITER, email)
        repo.add_user(user)
    return AccountOut(
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
        organization=organization,
        full_name=full_name,
    )


@router.get("/session", response_model=SessionOut)
def session(
    user: User = Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
) -> SessionOut:
    permissions = [
        permission.value
        for permission in Permission
        if not _denies(auth, user, permission)
    ]
    return SessionOut(
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
        permissions=permissions,
    )


def _denies(auth: AuthService, user: User, permission: Permission) -> bool:
    try:
        auth.require(user, permission)
    except ForbiddenError:
        return True
    return False


@router.post(
    "/ingest",
    response_model=list[UploadStatusOut],
    status_code=status.HTTP_201_CREATED,
)
async def ingest_resumes(
    files: list[UploadFile] = File(...),
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    user: User = Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
    repo: SQLiteRepository = Depends(get_repo),
    storage: StoragePort = Depends(get_storage),
    index: LocalHybridIndex = Depends(get_index),
    settings: Settings = Depends(get_settings),
) -> list[UploadStatusOut]:
    _require(auth, user, Permission.APPLICATION_CREATE)
    service = IngestionService(DocumentParser(storage), OfflineExtractor(), repo, index)
    queue = LocalAsyncQueue(service.process_job, max_batch_size=settings.max_batch_size)

    accepted: list[tuple[str, str, bool, bytes]] = []
    result: list[UploadStatusOut] = []
    for item in files:
        raw = await item.read()
        filename = item.filename or "upload"
        error = _validate_upload(filename, raw)
        if error:
            result.append(
                UploadStatusOut(
                    filename=filename,
                    file_hash=hashlib.sha256(raw).hexdigest(),
                    status=IngestionStatus.FAILED,
                    duplicate=False,
                    error=error,
                )
            )
            continue
        digest = hashlib.sha256(raw).hexdigest()
        duplicate = repo.get_candidate_by_hash(x_tenant_id, digest) is not None
        accepted.append((filename, digest, duplicate, raw))

    try:
        job_ids = queue.enqueue_batch(
            x_tenant_id,
            [DocumentUpload(name, raw) for name, _, _, raw in accepted],
        )
    except QueueLimitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    while queue.process_next():
        pass
    for job_id, (filename, digest, duplicate, _) in zip(job_ids, accepted):
        job = queue.get_job(job_id)
        record = repo.get_candidate_by_hash(x_tenant_id, digest)
        assert job is not None
        result.append(
            UploadStatusOut(
                filename=filename,
                file_hash=digest,
                status=job.status,
                duplicate=duplicate,
                candidate_id=record.id if record else None,
                error=job.error,
            )
        )
    return result


@router.get("/insights", response_model=InsightsOut)
def hiring_insights(
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    user: User = Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
    repo: SQLiteRepository = Depends(get_repo),
) -> InsightsOut:
    _require(auth, user, Permission.APPLICATION_READ)
    return InsightsOut(**asdict(InsightsService(repo).summarize(x_tenant_id)))


@router.get("/candidates", response_model=list[CandidateReviewOut])
def review_candidates(
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    user: User = Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
    repo: SQLiteRepository = Depends(get_repo),
) -> list[CandidateReviewOut]:
    _require(auth, user, Permission.APPLICATION_READ)
    scoring_by_application = repo.list_scoring_results(x_tenant_id)
    by_candidate: dict[str, list[ApplicationSummaryOut]] = {}
    for application in repo.list_applications(x_tenant_id):
        scoring = scoring_by_application.get(application.id)
        by_candidate.setdefault(application.candidate_id, []).append(
            ApplicationSummaryOut(
                id=application.id,
                job_id=application.job_id,
                stage=application.stage,
                scoring=_scoring_out(scoring) if scoring else None,
            )
        )

    result: list[CandidateReviewOut] = []
    for record in repo.list_candidates(x_tenant_id):
        summaries = by_candidate.get(record.id, [])
        stages = {item.stage for item in summaries}
        hide = _masked(user.role, stages)
        profile = record.profile
        result.append(
            CandidateReviewOut(
                candidate_id=record.id,
                full_name=profile.full_name,
                email=_mask_email(profile.email) if hide else profile.email,
                phone="*" * len(profile.phone) if hide else profile.phone,
                skills=profile.skills,
                total_experience_years=profile.total_experience_years,
                raw_text=profile.raw_text or "\n".join(profile.raw_chunks),
                pii_masked=hide,
                applications=summaries,
            )
        )
    return result


@router.post("/scoring", response_model=ScoringResultOut)
def score_application(
    payload: ScoreRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    user: User = Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
    repo: SQLiteRepository = Depends(get_repo),
) -> ScoringResultOut:
    _require(auth, user, Permission.APPLICATION_READ)
    application: Application | None = repo.get_application(
        x_tenant_id, payload.application_id
    )
    if application is None:
        raise HTTPException(status_code=404, detail="application not found in this tenant")
    candidate = repo.get_candidate(x_tenant_id, application.candidate_id)
    job = repo.get_job(x_tenant_id, application.job_id)
    if candidate is None or job is None:
        raise HTTPException(status_code=404, detail="candidate or job not found in this tenant")
    evaluations = [CriterionEvaluation(**item.model_dump()) for item in payload.evaluations]
    scored = ScoringService(CitationVerifier(), PIIRedactor(), repo).score(
        application=application,
        candidate=candidate.profile,
        job=job,
        evaluations=evaluations,
        blind_mode=payload.blind_mode,
    )
    return _scoring_out(scored)
