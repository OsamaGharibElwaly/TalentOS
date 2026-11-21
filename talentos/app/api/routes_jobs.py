from dataclasses import asdict

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_user, get_job_service
from app.domain.exceptions import (
    ForbiddenError,
    NotFoundError,
    RubricValidationError,
    TenantMismatchError,
)
from app.domain.models import Job, RubricCriterion, User
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


class RubricCriterionIn(BaseModel):
    id: str
    name: str
    weight: float
    description: str = ""


class JobCreateIn(BaseModel):
    title: str
    description: str = ""
    rubric: list[RubricCriterionIn]


class JobOut(BaseModel):
    id: str
    tenant_id: str
    title: str
    description: str
    created_by: str
    rubric: list[RubricCriterionIn]


def _to_out(job: Job) -> JobOut:
    return JobOut(
        id=job.id,
        tenant_id=job.tenant_id,
        title=job.title,
        description=job.description,
        created_by=job.created_by,
        rubric=[RubricCriterionIn(**asdict(c)) for c in job.rubric],
    )


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreateIn,
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    user: User = Depends(get_current_user),
    jobs: JobService = Depends(get_job_service),
) -> JobOut:
    criteria = [RubricCriterion(**c.model_dump()) for c in payload.rubric]
    try:
        job = jobs.create_job(
            user=user,
            tenant_id=x_tenant_id,
            title=payload.title,
            description=payload.description,
            rubric=criteria,
        )
    except RubricValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (ForbiddenError, TenantMismatchError) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return _to_out(job)


@router.get("", response_model=list[JobOut])
def list_jobs(
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    user: User = Depends(get_current_user),
    jobs: JobService = Depends(get_job_service),
) -> list[JobOut]:
    try:
        found = jobs.list_jobs(user=user, tenant_id=x_tenant_id)
    except (ForbiddenError, TenantMismatchError) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return [_to_out(job) for job in found]


@router.get("/{job_id}", response_model=JobOut)
def get_job(
    job_id: str,
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    user: User = Depends(get_current_user),
    jobs: JobService = Depends(get_job_service),
) -> JobOut:
    try:
        job = jobs.get_job(user=user, tenant_id=x_tenant_id, job_id=job_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ForbiddenError, TenantMismatchError) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return _to_out(job)
