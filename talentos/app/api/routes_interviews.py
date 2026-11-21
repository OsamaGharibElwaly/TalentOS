from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_auth_service, get_current_user, get_repo
from app.domain.enums import Permission
from app.domain.exceptions import ForbiddenError
from app.domain.models import InterviewQuestion, InterviewScorecard, User
from app.ports.repositories import RepositoryPort
from app.services.auth_service import AuthService
from app.services.interview_copilot import InterviewCopilot

router = APIRouter(prefix="/interviews", tags=["interviews"])


class QuestionRequest(BaseModel):
    candidate_id: str
    job_id: str
    application_id: str | None = None


class ScorecardRequest(BaseModel):
    candidate_id: str
    job_id: str
    raw_notes: str


def _require(auth: AuthService, user: User, permission: Permission) -> None:
    try:
        auth.require(user, permission)
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/questions", response_model=list[InterviewQuestion])
def generate_questions(
    payload: QuestionRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    user: User = Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
    repo: RepositoryPort = Depends(get_repo),
) -> list[InterviewQuestion]:
    _require(auth, user, Permission.APPLICATION_READ)
    candidate = repo.get_candidate(x_tenant_id, payload.candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="candidate not found in this tenant")
    job = repo.get_job(x_tenant_id, payload.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found in this tenant")
    scoring = None
    if payload.application_id:
        application = repo.get_application(x_tenant_id, payload.application_id)
        if application is None:
            raise HTTPException(status_code=404, detail="application not found in this tenant")
        scoring = repo.get_scoring_result(payload.application_id)
    return InterviewCopilot().generate_questions(candidate.profile, job, scoring)


@router.post("/scorecards", response_model=InterviewScorecard, status_code=status.HTTP_201_CREATED)
def synthesize_scorecard(
    payload: ScorecardRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    user: User = Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
    repo: RepositoryPort = Depends(get_repo),
) -> InterviewScorecard:
    _require(auth, user, Permission.APPLICATION_READ)
    candidate = repo.get_candidate(x_tenant_id, payload.candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="candidate not found in this tenant")
    job = repo.get_job(x_tenant_id, payload.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found in this tenant")
    return InterviewCopilot().synthesize_notes(
        payload.raw_notes,
        candidate.profile,
        job,
        candidate_id=payload.candidate_id,
    )
