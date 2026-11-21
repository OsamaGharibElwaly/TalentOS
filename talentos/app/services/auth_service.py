from app.domain.enums import Permission, Role
from app.domain.exceptions import ForbiddenError, TenantMismatchError
from app.domain.models import User
from app.ports.repositories import RepositoryPort

_ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset(Permission),
    Role.RECRUITER: frozenset(
        {
            Permission.JOB_CREATE,
            Permission.JOB_READ,
            Permission.APPLICATION_CREATE,
            Permission.APPLICATION_READ,
        }
    ),
    Role.HIRING_MANAGER: frozenset({Permission.JOB_READ, Permission.APPLICATION_READ}),
    Role.VIEWER: frozenset({Permission.JOB_READ}),
}


class AuthService:
    def __init__(self, repo: RepositoryPort) -> None:
        self._repo = repo

    def authenticate(self, user_id: str, tenant_id: str) -> User:
        user = self._repo.get_user(user_id)
        if user is None:
            raise ForbiddenError("unknown user")
        if user.tenant_id != tenant_id:
            raise TenantMismatchError("user does not belong to the requested tenant")
        return user

    def require(self, user: User, permission: Permission) -> None:
        if permission not in _ROLE_PERMISSIONS.get(user.role, frozenset()):
            raise ForbiddenError(f"{user.role.value} cannot {permission.value}")
