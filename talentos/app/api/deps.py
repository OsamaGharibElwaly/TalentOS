from functools import lru_cache

from fastapi import Depends, Header, HTTPException

from app.adapters.local_hybrid_index import LocalHybridIndex
from app.adapters.local_storage import LocalStorage
from app.adapters.sqlite_repo import SQLiteRepository
from app.config import Settings
from app.domain.exceptions import ForbiddenError, TenantMismatchError
from app.domain.models import User
from app.ports.storage import StoragePort
from app.services.auth_service import AuthService
from app.services.job_service import JobService


@lru_cache(maxsize=1)
def resources() -> tuple[
    Settings, SQLiteRepository, AuthService, JobService, StoragePort, LocalHybridIndex
]:
    settings = Settings.from_env()
    repo = SQLiteRepository(settings.db_path)
    auth = AuthService(repo)
    jobs = JobService(repo, auth, tolerance=settings.rubric_tolerance)
    storage: StoragePort = LocalStorage(settings.storage_dir)
    index = LocalHybridIndex(settings.index_path)
    return settings, repo, auth, jobs, storage, index


def get_settings() -> Settings:
    return resources()[0]


def get_repo() -> SQLiteRepository:
    return resources()[1]


def get_auth_service() -> AuthService:
    return resources()[2]


def get_job_service() -> JobService:
    return resources()[3]


def get_storage() -> StoragePort:
    return resources()[4]


def get_index() -> LocalHybridIndex:
    return resources()[5]


def get_current_user(
    x_user_id: str = Header(..., alias="X-User-Id"),
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    auth: AuthService = Depends(get_auth_service),
) -> User:
    try:
        return auth.authenticate(x_user_id, x_tenant_id)
    except (ForbiddenError, TenantMismatchError) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
