from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from app.domain.enums import ApplicationStage
from app.domain.exceptions import ForbiddenError, InvalidStageTransitionError, NotFoundError
from app.domain.models import Application, AuditLog, StageRecommendation, User
from app.ports.repositories import RepositoryPort

ALLOWED_TRANSITIONS: dict[ApplicationStage, frozenset[ApplicationStage]] = {
    ApplicationStage.NEW: frozenset({ApplicationStage.SCREENED, ApplicationStage.REJECTED}),
    ApplicationStage.SCREENED: frozenset({ApplicationStage.SHORTLISTED, ApplicationStage.REJECTED}),
    ApplicationStage.SHORTLISTED: frozenset({ApplicationStage.INTERVIEW, ApplicationStage.REJECTED}),
    ApplicationStage.INTERVIEW: frozenset({ApplicationStage.FINAL_REVIEW, ApplicationStage.REJECTED}),
    ApplicationStage.FINAL_REVIEW: frozenset({ApplicationStage.OFFER, ApplicationStage.REJECTED}),
    ApplicationStage.OFFER: frozenset(),
    ApplicationStage.REJECTED: frozenset(),
}
HUMAN_CONFIRMATION_STAGES = frozenset({ApplicationStage.OFFER, ApplicationStage.REJECTED})


class PipelineService:
    """Stage machine where only a confirmed human actor may persist OFFER/REJECTED."""

    def __init__(self, repo: RepositoryPort) -> None:
        self._repo = repo

    def transition(
        self,
        *,
        tenant_id: str,
        application_id: str,
        actor: User,
        to_stage: ApplicationStage,
        reason: str = "",
        confirm: bool = False,
    ) -> Application:
        application = self._repo.get_application(tenant_id, application_id)
        if application is None:
            raise NotFoundError("application not found in this tenant")
        if actor.tenant_id != tenant_id:
            raise ForbiddenError("actor does not belong to the requested tenant")
        if to_stage not in ALLOWED_TRANSITIONS[application.stage]:
            raise InvalidStageTransitionError(
                f"{application.stage.value} -> {to_stage.value} is not a valid transition"
            )
        if to_stage in HUMAN_CONFIRMATION_STAGES and not (confirm and reason.strip()):
            raise ForbiddenError(
                f"{to_stage.value} requires explicit human confirmation and a reason"
            )

        self._repo.update_application_stage(tenant_id, application_id, to_stage)
        self._repo.add_audit_log(
            AuditLog(
                id=str(uuid4()),
                tenant_id=tenant_id,
                application_id=application_id,
                from_stage=application.stage,
                to_stage=to_stage,
                actor_id=actor.id,
                reason=reason,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
        )
        return replace(application, stage=to_stage)

    def recommend(
        self,
        *,
        tenant_id: str,
        application_id: str,
        to_stage: ApplicationStage,
        rationale: str,
    ) -> StageRecommendation:
        application = self._repo.get_application(tenant_id, application_id)
        if application is None:
            raise NotFoundError("application not found in this tenant")
        return StageRecommendation(
            application_id=application_id,
            from_stage=application.stage,
            to_stage=to_stage,
            rationale=rationale,
            requires_human_confirmation=to_stage in HUMAN_CONFIRMATION_STAGES,
        )
