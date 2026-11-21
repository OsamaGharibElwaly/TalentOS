from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_auth_service, get_current_user, get_repo
from app.domain.enums import ApplicationStage, Permission, Role
from app.domain.exceptions import ForbiddenError, InvalidStageTransitionError, NotFoundError
from app.domain.models import Application, CandidateRecord, User
from app.ports.repositories import RepositoryPort
from app.services.auth_service import AuthService
from app.services.pipeline_service import PipelineService

router = APIRouter(prefix="/applications", tags=["applications"])
MASKED_STAGES = {ApplicationStage.NEW, ApplicationStage.SCREENED, ApplicationStage.REJECTED}


class ApplicationCreateIn(BaseModel):
    candidate_id: str
    job_id: str


class TransitionIn(BaseModel):
    to_stage: ApplicationStage
    reason: str = ""
    confirm: bool = False


class ApplicationOut(BaseModel):
    id: str
    tenant_id: str
    candidate_id: str
    job_id: str
    stage: ApplicationStage
    created_at: str
    full_name: str
    email: str
    phone: str


def _mask_email(value: str) -> str:
    local, separator, domain = value.partition("@")
    return f"{local[:1]}***@{domain}" if separator else "***"


def _to_out(
    application: Application, candidate: CandidateRecord, *, mask_pii: bool
) -> ApplicationOut:
    profile = candidate.profile
    return ApplicationOut(
        id=application.id,
        tenant_id=application.tenant_id,
        candidate_id=application.candidate_id,
        job_id=application.job_id,
        stage=application.stage,
        created_at=application.created_at,
        full_name=profile.full_name,
        email=_mask_email(profile.email) if mask_pii else profile.email,
        phone="*" * len(profile.phone) if mask_pii else profile.phone,
    )


def _require(auth: AuthService, user: User, permission: Permission) -> None:
    try:
        auth.require(user, permission)
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreateIn,
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    user: User = Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
    repo: RepositoryPort = Depends(get_repo),
) -> ApplicationOut:
    _require(auth, user, Permission.APPLICATION_CREATE)
    candidate = repo.get_candidate(x_tenant_id, payload.candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="candidate not found in this tenant")
    application = Application(
        id=str(uuid4()),
        tenant_id=x_tenant_id,
        candidate_id=payload.candidate_id,
        job_id=payload.job_id,
        stage=ApplicationStage.NEW,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    repo.add_application(application)
    return _to_out(application, candidate, mask_pii=False)


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(
    application_id: str,
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    user: User = Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
    repo: RepositoryPort = Depends(get_repo),
) -> ApplicationOut:
    _require(auth, user, Permission.APPLICATION_READ)
    application = repo.get_application(x_tenant_id, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="application not found in this tenant")
    candidate = repo.get_candidate(x_tenant_id, application.candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="candidate not found in this tenant")
    mask_pii = user.role == Role.HIRING_MANAGER and application.stage in MASKED_STAGES
    return _to_out(application, candidate, mask_pii=mask_pii)


@router.post("/{application_id}/transition", response_model=ApplicationOut)
def transition_application(
    application_id: str,
    payload: TransitionIn,
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    user: User = Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
    repo: RepositoryPort = Depends(get_repo),
) -> ApplicationOut:
    _require(auth, user, Permission.APPLICATION_READ)
    try:
        updated = PipelineService(repo).transition(
            tenant_id=x_tenant_id,
            application_id=application_id,
            actor=user,
            to_stage=payload.to_stage,
            reason=payload.reason,
            confirm=payload.confirm,
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (InvalidStageTransitionError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    candidate = repo.get_candidate(x_tenant_id, updated.candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="candidate not found in this tenant")
    return _to_out(updated, candidate, mask_pii=False)
