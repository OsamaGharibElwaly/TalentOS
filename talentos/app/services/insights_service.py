from __future__ import annotations

from collections import Counter

from app.domain.enums import ApplicationStage
from app.domain.models import HiringInsights, InsightDecision, InsightRank
from app.ports.repositories import RepositoryPort

READY_STAGES = frozenset(
    {
        ApplicationStage.SHORTLISTED,
        ApplicationStage.INTERVIEW,
        ApplicationStage.FINAL_REVIEW,
    }
)


class InsightsService:
    """Builds tenant-scoped hiring analysis and plain-language next steps."""

    def __init__(self, repo: RepositoryPort) -> None:
        self._repo = repo

    def summarize(self, tenant_id: str) -> HiringInsights:
        candidates = self._repo.list_candidates(tenant_id)
        applications = self._repo.list_applications(tenant_id)
        scores = self._repo.list_scoring_results(tenant_id)

        by_stage = {stage.value: 0 for stage in ApplicationStage}
        for application in applications:
            by_stage[application.stage.value] += 1

        scored = [scores[item.id] for item in applications if item.id in scores]
        average = (
            round(sum(item.composite_score for item in scored) / len(scored), 3)
            if scored
            else 0.0
        )

        skill_counts = Counter(
            skill for candidate in candidates for skill in candidate.profile.skills
        )
        top_skills = [
            InsightRank(label=name, value=float(count))
            for name, count in skill_counts.most_common(5)
        ]

        names = {item.id: item.profile.full_name for item in candidates}
        ready = sorted(
            (
                InsightRank(
                    label=names.get(application.candidate_id, application.candidate_id),
                    value=round(scores[application.id].composite_score, 3),
                )
                for application in applications
                if application.id in scores
                and application.stage in READY_STAGES
                and scores[application.id].composite_score >= 0.75
            ),
            key=lambda item: item.value,
            reverse=True,
        )[:3]
        needs_review = sum(1 for item in scored if item.composite_score < 0.5)

        decisions: list[InsightDecision] = []
        awaiting_first_look = by_stage["NEW"] + by_stage["SCREENED"]
        if awaiting_first_look:
            decisions.append(
                InsightDecision(
                    title="Give new applicants a first look",
                    detail=f"{awaiting_first_look} people are waiting for a first review.",
                    href="/candidates",
                    tone="indigo",
                )
            )
        in_interview = by_stage["SHORTLISTED"] + by_stage["INTERVIEW"]
        if in_interview:
            decisions.append(
                InsightDecision(
                    title="Prepare your next interviews",
                    detail=f"{in_interview} people are shortlisted or interviewing.",
                    href="/interviews",
                    tone="teal",
                )
            )
        if needs_review:
            noun = "review" if needs_review == 1 else "reviews"
            verb = "needs" if needs_review == 1 else "need"
            decisions.append(
                InsightDecision(
                    title="Double-check lower scores",
                    detail=f"{needs_review} {noun} {verb} a second look before a decision.",
                    href="/candidates",
                    tone="amber",
                )
            )
        if by_stage["OFFER"]:
            offers = by_stage["OFFER"]
            noun = "offer" if offers == 1 else "offers"
            verb = "is" if offers == 1 else "are"
            decisions.append(
                InsightDecision(
                    title="Follow up on offers",
                    detail=f"{offers} {noun} {verb} in progress.",
                    href="/telemetry",
                    tone="rose",
                )
            )
        if not decisions:
            decisions.append(
                InsightDecision(
                    title="Set up your first role",
                    detail="Describe a role and add a resume to start a pipeline.",
                    href="/jobs",
                    tone="violet",
                )
            )

        return HiringInsights(
            tenant_id=tenant_id,
            candidates=len(candidates),
            applications=len(applications),
            by_stage=by_stage,
            average_score=average,
            scored_applications=len(scored),
            top_skills=top_skills,
            ready_to_interview=ready,
            needs_review=needs_review,
            decisions=decisions[:3],
        )
