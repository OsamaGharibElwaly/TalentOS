from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_auth_service, get_current_user, get_repo
from app.domain.enums import Permission
from app.domain.exceptions import ForbiddenError
from app.domain.models import TelemetrySummary, User
from app.ports.repositories import RepositoryPort
from app.services.auth_service import AuthService
from app.services.telemetry_service import TelemetryService

router = APIRouter(prefix="/api/v1/telemetry", tags=["telemetry"])


@router.get("/summary", response_model=TelemetrySummary)
def telemetry_summary(
    user: User = Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
    repo: RepositoryPort = Depends(get_repo),
) -> TelemetrySummary:
    try:
        auth.require(user, Permission.TELEMETRY_READ)
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return TelemetryService(repo).summary(user.tenant_id)
