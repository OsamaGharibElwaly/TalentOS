from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.adapters.local_hybrid_index import LocalHybridIndex
from app.api.deps import get_auth_service, get_current_user, get_index, get_repo
from app.domain.enums import ApplicationStage, Permission
from app.domain.exceptions import ForbiddenError
from app.domain.models import TalentSearchResult, User
from app.ports.repositories import RepositoryPort
from app.services.auth_service import AuthService
from app.services.talent_search_service import TalentSearchService

router = APIRouter(prefix="/search", tags=["search"])


class TalentSearchIn(BaseModel):
    query: str
    min_experience_years: float | None = None
    required_skills: list[str] = Field(default_factory=list)
    stage: ApplicationStage | None = None
    top_k: int = 10


@router.post("/talent", response_model=list[TalentSearchResult])
def search_talent(
    payload: TalentSearchIn,
    user: User = Depends(get_current_user),
    auth: AuthService = Depends(get_auth_service),
    repo: RepositoryPort = Depends(get_repo),
    index: LocalHybridIndex = Depends(get_index),
) -> list[TalentSearchResult]:
    try:
        auth.require(user, Permission.APPLICATION_READ)
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return TalentSearchService(repo, index).search(
        user.tenant_id,
        payload.query,
        min_experience_years=payload.min_experience_years,
        required_skills=payload.required_skills,
        stage=payload.stage,
        top_k=payload.top_k,
    )
