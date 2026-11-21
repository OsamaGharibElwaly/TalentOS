from uuid import uuid4

from app.domain.enums import Permission
from app.domain.exceptions import (
    NotFoundError,
    RubricValidationError,
    TenantMismatchError,
)
from app.domain.models import Job, RubricCriterion, User
from app.ports.repositories import RepositoryPort
from app.services.auth_service import AuthService

DEFAULT_RUBRIC_TOLERANCE = 1e-6


def validate_rubric(
    criteria: list[RubricCriterion], *, tolerance: float = DEFAULT_RUBRIC_TOLERANCE
) -> None:
    if not criteria:
        raise RubricValidationError("a job rubric needs at least one criterion")
    total = 0.0
    seen: set[str] = set()
    for item in criteria:
        if not item.name.strip():
            raise RubricValidationError("criterion names cannot be empty")
        if item.id in seen:
            raise RubricValidationError(f"duplicate criterion id: {item.id}")
        seen.add(item.id)
        if item.weight <= 0.0:
            raise RubricValidationError(f"criterion {item.id} must have a positive weight")
        total += item.weight
    if abs(total - 1.0) > tolerance:
        raise RubricValidationError(f"rubric weights must sum to 1.0 (got {total:.6f})")


class JobService:
    def __init__(
        self,
        repo: RepositoryPort,
        auth: AuthService,
        *,
        tolerance: float = DEFAULT_RUBRIC_TOLERANCE,
    ) -> None:
        self._repo = repo
        self._auth = auth
        self._tolerance = tolerance

    def create_job(
        self,
        *,
        user: User,
        tenant_id: str,
        title: str,
        rubric: list[RubricCriterion],
        description: str = "",
    ) -> Job:
        self._auth.require(user, Permission.JOB_CREATE)
        self._assert_tenant(user, tenant_id)
        validate_rubric(rubric, tolerance=self._tolerance)
        job = Job(
            id=str(uuid4()),
            tenant_id=tenant_id,
            title=title,
            description=description,
            created_by=user.id,
            rubric=list(rubric),
        )
        self._repo.add_job(job)
        return job

    def get_job(self, *, user: User, tenant_id: str, job_id: str) -> Job:
        self._auth.require(user, Permission.JOB_READ)
        self._assert_tenant(user, tenant_id)
        job = self._repo.get_job(tenant_id, job_id)
        if job is None:
            raise NotFoundError("job not found in this tenant")
        return job

    def list_jobs(self, *, user: User, tenant_id: str) -> list[Job]:
        self._auth.require(user, Permission.JOB_READ)
        self._assert_tenant(user, tenant_id)
        return self._repo.list_jobs(tenant_id)

    @staticmethod
    def _assert_tenant(user: User, tenant_id: str) -> None:
        if user.tenant_id != tenant_id:
            raise TenantMismatchError("user cannot access another tenant's jobs")
