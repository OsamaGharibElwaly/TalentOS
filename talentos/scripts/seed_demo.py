"""Idempotent local demo data for the HR workspace.

Run from talentos/: python -m scripts.seed_demo
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.adapters.local_hybrid_index import LocalHybridIndex
from app.adapters.sqlite_repo import SQLiteRepository
from app.config import Settings
from app.domain.enums import ApplicationStage, Role
from app.domain.models import (
    Application,
    AuditLog,
    CandidateProfile,
    CandidateRecord,
    Citation,
    CriterionScore,
    ExperienceEntry,
    GapProbe,
    Job,
    RubricCriterion,
    ScoringResult,
    TelemetryEvent,
    Tenant,
    User,
)
from app.ports.repositories import RepositoryPort
from app.services.telemetry_service import TelemetryService

TENANT_ID = "org-1"
NOW = "2026-11-20T09:00:00+00:00"

JOBS = (
    Job(
        id="job-1",
        tenant_id=TENANT_ID,
        title="Senior Backend Engineer",
        description="Own Python services and data APIs.",
        created_by="admin",
        rubric=[
            RubricCriterion("crit-1", "Backend engineering", 0.6, "Builds reliable services", True),
            RubricCriterion("crit-2", "Data and SQL", 0.4, "Works confidently with data", False),
        ],
    ),
    Job(
        id="job-2",
        tenant_id=TENANT_ID,
        title="Product Designer",
        description="Turn research into calm, usable screens.",
        created_by="admin",
        rubric=[
            RubricCriterion("design-1", "User research", 0.5, "Understands real users", True),
            RubricCriterion("design-2", "Design craft", 0.5, "Clear, consistent visuals", False),
        ],
    ),
    Job(
        id="job-3",
        tenant_id=TENANT_ID,
        title="Data Analyst",
        description="Turn raw numbers into decisions people can act on.",
        created_by="admin",
        rubric=[
            RubricCriterion("data-1", "Analysis", 0.6, "Finds the signal in the data", True),
            RubricCriterion("data-2", "Communication", 0.4, "Explains findings plainly", False),
        ],
    ),
)

CANDIDATES = (
    ("cand-1", "Alice Rivera", ("python", "sql", "fastapi"), 8, "NEW", 0.88, "job-1"),
    ("cand-2", "Daniel Okafor", ("python", "sql", "aws", "docker"), 6, "SCREENED", 0.82, "job-1"),
    ("cand-3", "Priya Shah", ("python", "fastapi", "postgresql", "testing"), 5, "SHORTLISTED", 0.91, "job-1"),
    ("cand-4", "Marta Nowak", ("ux research", "figma", "prototyping"), 7, "INTERVIEW", 0.86, "job-2"),
    ("cand-5", "Liam Chen", ("figma", "design systems", "user testing"), 4, "FINAL_REVIEW", 0.79, "job-2"),
    ("cand-6", "Sofia Alvarez", ("sql", "python", "statistics", "dashboards"), 6, "OFFER", 0.93, "job-3"),
    ("cand-7", "Noah Williams", ("sql", "excel", "reporting"), 3, "NEW", 0.62, "job-3"),
    ("cand-8", "Amina Hassan", ("python", "sql", "spark", "airflow"), 9, "SCREENED", 0.74, "job-3"),
    ("cand-9", "Tom Becker", ("javascript", "react", "node"), 5, "REJECTED", 0.41, "job-1"),
)


def _resume_text(name: str, email: str, years: int, skills: tuple[str, ...]) -> str:
    first, second = skills[0], skills[1]
    return (
        f"{name}\n{email}\n{years} years of experience.\n\n"
        f"SKILLS\n{', '.join(skills)}\n\n"
        f"EXPERIENCE\nSenior Specialist | Example Co | {years * 6} months\n"
        f"- Worked with {first} and {second} to deliver projects.\n"
        "- Improved reporting, documentation and team handovers.\n"
    )


def _profile(item: tuple[str, str, tuple[str, ...], int, str, float, str]) -> CandidateProfile:
    _, name, skills, years, _, _, _ = item
    email = f"{name.lower().replace(' ', '.')}@example.com"
    text = _resume_text(name, email, years, skills)
    return CandidateProfile(
        full_name=name,
        email=email,
        phone="+1 555 0100",
        links=[],
        total_experience_years=float(years),
        skills=list(skills),
        experience_entries=[
            ExperienceEntry(
                title="Senior Specialist",
                company="Example Co",
                duration_months=years * 6,
                highlights=[f"Delivered projects with {skills[0]}.", "Improved reporting."],
            )
        ],
        education=[],
        raw_chunks=[text],
        raw_text=text,
    )


def seed(
    repo: RepositoryPort,
    *,
    tenant_id: str = TENANT_ID,
    index: LocalHybridIndex | None = None,
) -> dict[str, int]:
    """Add the demo workspace without duplicating records on repeated runs."""
    counts = {"jobs": 0, "candidates": 0, "applications": 0, "scores": 0, "events": 0}

    if repo.get_tenant(tenant_id) is None:
        repo.add_tenant(Tenant(tenant_id, "People First Ltd"))
    for user_id, role in (
        ("admin", Role.ADMIN),
        ("recruiter", Role.RECRUITER),
        ("manager", Role.HIRING_MANAGER),
        ("viewer", Role.VIEWER),
    ):
        if repo.get_user(user_id) is None:
            repo.add_user(User(user_id, tenant_id, role, f"{user_id}@example.com"))

    for job in JOBS:
        if repo.get_job(tenant_id, job.id) is None:
            repo.add_job(job)
            counts["jobs"] += 1

    for item in CANDIDATES:
        candidate_id, name, skills, years, stage, score, job_id = item
        profile = _profile(item)
        if repo.get_candidate(tenant_id, candidate_id) is None:
            record = CandidateRecord(
                id=candidate_id,
                tenant_id=tenant_id,
                file_hash=f"demo-{candidate_id}",
                filename=f"{candidate_id}.txt",
                storage_key=f"demo/{candidate_id}.txt",
                profile=profile,
                created_at=NOW,
                updated_at=NOW,
            )
            repo.upsert_candidate(record)
            counts["candidates"] += 1
        if index is not None:
            index.upsert(
                doc_id=candidate_id,
                tenant_id=tenant_id,
                text=profile.raw_text,
                metadata={
                    "filename": f"{candidate_id}.txt",
                    "file_hash": f"demo-{candidate_id}",
                    "full_name": name,
                    "skills": list(skills),
                },
            )

        application_id = candidate_id.replace("cand-", "app-")
        if repo.get_application(tenant_id, application_id) is None:
            repo.add_application(
                Application(application_id, tenant_id, candidate_id, job_id, ApplicationStage(stage), NOW)
            )
            counts["applications"] += 1
        job = repo.get_job(tenant_id, job_id)
        assert job is not None
        quote = f"- Worked with {skills[0]} and {skills[1]} to deliver projects."
        criterion_scores = [
            CriterionScore(
                criterion_id=criterion.id,
                criterion_name=criterion.name,
                weight=criterion.weight,
                score=int(score * 100) - (index_offset * 3),
                rationale=f"Resume mentions {skills[0]} and {skills[1]}.",
                citations=[Citation(quote, True, 0.95)],
                confidence=0.95,
            )
            for index_offset, criterion in enumerate(job.rubric)
        ]
        if repo.get_scoring_result(application_id) is None:
            repo.save_scoring_result(
                ScoringResult(
                    application_id=application_id,
                    candidate_id=candidate_id,
                    composite_score=score,
                    criterion_scores=criterion_scores,
                    gaps_and_probes=(
                        [GapProbe("evidence", job.rubric[0].id, "Add a concrete example.")]
                        if score < 0.7
                        else []
                    ),
                    blind_mode=False,
                )
            )
            counts["scores"] += 1
        if stage != "NEW":
            audit_id = f"audit-demo-{candidate_id}"
            if not any(
                item.id == audit_id for item in repo.list_audit_logs(tenant_id, application_id)
            ):
                repo.add_audit_log(
                    AuditLog(
                        audit_id,
                        tenant_id,
                        application_id,
                        ApplicationStage.NEW,
                        ApplicationStage(stage),
                        "recruiter",
                        "Demo pipeline history",
                        NOW,
                    )
                )

    if not repo.list_telemetry(tenant_id):
        service = TelemetryService(repo)
        operations = ("ingest", "score", "score", "search", "transition", "interview_questions")
        for offset in range(12):
            service.track(
                tenant_id=tenant_id,
                operation=operations[offset % len(operations)],
                latency_ms=12.0 + offset * 1.5,
                tokens_in=180 + offset * 7,
                tokens_out=30 + offset * 2,
                citation_pass_rate=0.88 + (offset % 5) * 0.02,
                status="error" if offset == 4 else "ok",
            )
        counts["events"] = 12
    return counts


def main() -> None:
    settings = Settings.from_env()
    repo = SQLiteRepository(settings.db_path)
    index = LocalHybridIndex(settings.index_path)
    try:
        counts = seed(repo, tenant_id=TENANT_ID, index=index)
    finally:
        repo.close()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"Demo workspace ready at {stamp}: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    print("Sign in at http://localhost:3000/login with org-1 (try admin for insights).")


if __name__ == "__main__":
    main()
