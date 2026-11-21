import json
import sqlite3
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from app.domain.enums import ApplicationStage, Role
from app.domain.models import (
    Application,
    AuditLog,
    CandidateProfile,
    CandidateRecord,
    Citation,
    CriterionScore,
    EducationEntry,
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


class SQLiteRepository(RepositoryPort):
    """SQLite-backed RepositoryPort with tenant-scoped job reads."""

    def __init__(self, db_path: str | Path) -> None:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._create_schema()
        self._migrate()

    def _create_schema(self) -> None:
        with self._conn:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tenants (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    email TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    created_by TEXT NOT NULL,
                    rubric TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_jobs_tenant ON jobs(tenant_id);
                CREATE TABLE IF NOT EXISTS candidates (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    storage_key TEXT NOT NULL,
                    profile TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(tenant_id, file_hash)
                );
                CREATE INDEX IF NOT EXISTS idx_candidates_tenant ON candidates(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_candidates_tenant_hash
                    ON candidates(tenant_id, file_hash);
                CREATE TABLE IF NOT EXISTS applications (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    candidate_id TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_applications_tenant ON applications(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_applications_tenant_stage
                    ON applications(tenant_id, stage);
                CREATE TABLE IF NOT EXISTS scoring_results (
                    application_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL DEFAULT '',
                    job_id TEXT NOT NULL DEFAULT '',
                    total_score REAL NOT NULL DEFAULT 0,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    application_id TEXT NOT NULL,
                    from_stage TEXT NOT NULL,
                    to_stage TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    reason TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant_app
                    ON audit_logs(tenant_id, application_id);
                CREATE TABLE IF NOT EXISTS telemetry_events (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    tokens_in INTEGER NOT NULL,
                    tokens_out INTEGER NOT NULL,
                    citation_pass_rate REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_telemetry_tenant
                    ON telemetry_events(tenant_id);
                """
            )

    def _migrate(self) -> None:
        columns = {
            str(row["name"])
            for row in self._conn.execute("PRAGMA table_info(scoring_results)").fetchall()
        }
        with self._conn:
            for name, definition in (
                ("tenant_id", "TEXT NOT NULL DEFAULT ''"),
                ("job_id", "TEXT NOT NULL DEFAULT ''"),
                ("total_score", "REAL NOT NULL DEFAULT 0"),
            ):
                if name not in columns:
                    self._conn.execute(
                        f"ALTER TABLE scoring_results ADD COLUMN {name} {definition}"
                    )
            self._conn.execute(
                """CREATE INDEX IF NOT EXISTS idx_scoring_tenant_job_score
                   ON scoring_results(tenant_id, job_id, total_score)"""
            )
            self._conn.execute(
                """UPDATE scoring_results
                   SET tenant_id = COALESCE(
                         (SELECT tenant_id FROM applications
                          WHERE applications.id = scoring_results.application_id), ''),
                       job_id = COALESCE(
                         (SELECT job_id FROM applications
                          WHERE applications.id = scoring_results.application_id), '')
                   WHERE tenant_id = ''"""
            )

    def add_tenant(self, tenant: Tenant) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO tenants (id, name) VALUES (?, ?)",
                (tenant.id, tenant.name),
            )

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        row = self._conn.execute(
            "SELECT id, name FROM tenants WHERE id = ?", (tenant_id,)
        ).fetchone()
        return Tenant(id=row["id"], name=row["name"]) if row else None

    def add_user(self, user: User) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO users (id, tenant_id, role, email) VALUES (?, ?, ?, ?)",
                (user.id, user.tenant_id, user.role.value, user.email),
            )

    def get_user(self, user_id: str) -> User | None:
        row = self._conn.execute(
            "SELECT id, tenant_id, role, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if row is None:
            return None
        return User(
            id=row["id"],
            tenant_id=row["tenant_id"],
            role=Role(row["role"]),
            email=row["email"],
        )

    def add_job(self, job: Job) -> None:
        payload = json.dumps(
            [
                {
                    "id": c.id,
                    "name": c.name,
                    "weight": c.weight,
                    "description": c.description,
                    "mandatory": c.mandatory,
                }
                for c in job.rubric
            ]
        )
        with self._conn:
            self._conn.execute(
                """INSERT INTO jobs (id, tenant_id, title, description, created_by, rubric)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    job.id,
                    job.tenant_id,
                    job.title,
                    job.description,
                    job.created_by,
                    payload,
                ),
            )

    @staticmethod
    def _to_job(row: sqlite3.Row) -> Job:
        criteria = [RubricCriterion(**item) for item in json.loads(row["rubric"])]
        return Job(
            id=row["id"],
            tenant_id=row["tenant_id"],
            title=row["title"],
            description=row["description"],
            created_by=row["created_by"],
            rubric=criteria,
        )

    def get_job(self, tenant_id: str, job_id: str) -> Job | None:
        row = self._conn.execute(
            "SELECT * FROM jobs WHERE tenant_id = ? AND id = ?", (tenant_id, job_id)
        ).fetchone()
        return self._to_job(row) if row is not None else None

    def list_jobs(self, tenant_id: str) -> list[Job]:
        rows = self._conn.execute(
            "SELECT * FROM jobs WHERE tenant_id = ? ORDER BY id", (tenant_id,)
        ).fetchall()
        return [self._to_job(row) for row in rows]

    @staticmethod
    def _to_profile(data: dict[str, Any]) -> CandidateProfile:
        return CandidateProfile(
            full_name=str(data["full_name"]),
            email=str(data["email"]),
            phone=str(data["phone"]),
            links=[str(item) for item in data["links"]],
            total_experience_years=float(data["total_experience_years"]),
            skills=[str(item) for item in data["skills"]],
            experience_entries=[ExperienceEntry(**entry) for entry in data["experience_entries"]],
            education=[EducationEntry(**entry) for entry in data["education"]],
            raw_chunks=[str(item) for item in data["raw_chunks"]],
            raw_text=str(data.get("raw_text", "")),
        )

    @staticmethod
    def _to_candidate(row: sqlite3.Row) -> CandidateRecord:
        return CandidateRecord(
            id=row["id"],
            tenant_id=row["tenant_id"],
            file_hash=row["file_hash"],
            filename=row["filename"],
            storage_key=row["storage_key"],
            profile=SQLiteRepository._to_profile(json.loads(row["profile"])),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def upsert_candidate(self, candidate: CandidateRecord) -> CandidateRecord:
        payload = json.dumps(asdict(candidate.profile))
        with self._conn:
            existing = self._conn.execute(
                "SELECT id, created_at FROM candidates WHERE tenant_id = ? AND file_hash = ?",
                (candidate.tenant_id, candidate.file_hash),
            ).fetchone()
            if existing is None:
                candidate_id = candidate.id
                created_at = candidate.created_at
                self._conn.execute(
                    """INSERT INTO candidates
                       (id, tenant_id, file_hash, filename, storage_key, profile, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        candidate_id,
                        candidate.tenant_id,
                        candidate.file_hash,
                        candidate.filename,
                        candidate.storage_key,
                        payload,
                        created_at,
                        candidate.updated_at,
                    ),
                )
            else:
                candidate_id = existing["id"]
                created_at = existing["created_at"]
                self._conn.execute(
                    """UPDATE candidates
                       SET filename = ?, storage_key = ?, profile = ?, updated_at = ?
                       WHERE id = ?""",
                    (
                        candidate.filename,
                        candidate.storage_key,
                        payload,
                        candidate.updated_at,
                        candidate_id,
                    ),
                )
        return replace(candidate, id=candidate_id, created_at=created_at)

    def get_candidate(
        self, tenant_id: str, candidate_id: str
    ) -> CandidateRecord | None:
        row = self._conn.execute(
            "SELECT * FROM candidates WHERE tenant_id = ? AND id = ?",
            (tenant_id, candidate_id),
        ).fetchone()
        return self._to_candidate(row) if row is not None else None

    def get_candidate_by_hash(
        self, tenant_id: str, file_hash: str
    ) -> CandidateRecord | None:
        row = self._conn.execute(
            "SELECT * FROM candidates WHERE tenant_id = ? AND file_hash = ?",
            (tenant_id, file_hash),
        ).fetchone()
        return self._to_candidate(row) if row is not None else None

    def list_candidates(self, tenant_id: str) -> list[CandidateRecord]:
        rows = self._conn.execute(
            "SELECT * FROM candidates WHERE tenant_id = ? ORDER BY id", (tenant_id,)
        ).fetchall()
        return [self._to_candidate(row) for row in rows]

    def add_application(self, application: Application) -> None:
        with self._conn:
            self._conn.execute(
                """INSERT INTO applications (id, tenant_id, candidate_id, job_id, stage, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    application.id,
                    application.tenant_id,
                    application.candidate_id,
                    application.job_id,
                    application.stage.value,
                    application.created_at,
                ),
            )

    def get_application(
        self, tenant_id: str, application_id: str
    ) -> Application | None:
        row = self._conn.execute(
            "SELECT * FROM applications WHERE tenant_id = ? AND id = ?",
            (tenant_id, application_id),
        ).fetchone()
        if row is None:
            return None
        return Application(
            id=row["id"],
            tenant_id=row["tenant_id"],
            candidate_id=row["candidate_id"],
            job_id=row["job_id"],
            stage=ApplicationStage(row["stage"]),
            created_at=row["created_at"],
        )

    def save_scoring_result(self, result: ScoringResult) -> None:
        application = self._conn.execute(
            "SELECT tenant_id, job_id FROM applications WHERE id = ?",
            (result.application_id,),
        ).fetchone()
        tenant_id = str(application["tenant_id"]) if application else ""
        job_id = str(application["job_id"]) if application else ""
        with self._conn:
            self._conn.execute(
                """INSERT OR REPLACE INTO scoring_results
                   (application_id, tenant_id, job_id, total_score, payload)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    result.application_id,
                    tenant_id,
                    job_id,
                    result.composite_score,
                    json.dumps(asdict(result)),
                ),
            )

    @staticmethod
    def _to_scoring_result(payload: str) -> ScoringResult:
        data: dict[str, Any] = json.loads(payload)
        return ScoringResult(
            application_id=str(data["application_id"]),
            candidate_id=str(data["candidate_id"]),
            composite_score=float(data["composite_score"]),
            criterion_scores=[
                CriterionScore(
                    criterion_id=str(item["criterion_id"]),
                    criterion_name=str(item["criterion_name"]),
                    weight=float(item["weight"]),
                    score=int(item["score"]),
                    rationale=str(item["rationale"]),
                    citations=[
                        Citation(
                            quote=str(citation["quote"]),
                            verified=bool(citation["verified"]),
                            similarity=float(citation["similarity"]),
                        )
                        for citation in item["citations"]
                    ],
                    confidence=float(item["confidence"]),
                )
                for item in data["criterion_scores"]
            ],
            gaps_and_probes=[
                GapProbe(
                    kind=str(gap["kind"]),
                    criterion_id=str(gap["criterion_id"]),
                    detail=str(gap["detail"]),
                )
                for gap in data["gaps_and_probes"]
            ],
            blind_mode=bool(data["blind_mode"]),
        )

    def get_scoring_result(self, application_id: str) -> ScoringResult | None:
        row = self._conn.execute(
            "SELECT payload FROM scoring_results WHERE application_id = ?",
            (application_id,),
        ).fetchone()
        return self._to_scoring_result(row["payload"]) if row else None

    def list_scoring_results(self, tenant_id: str) -> dict[str, ScoringResult]:
        rows = self._conn.execute(
            "SELECT application_id, payload FROM scoring_results WHERE tenant_id = ?",
            (tenant_id,),
        ).fetchall()
        return {
            str(row["application_id"]): self._to_scoring_result(row["payload"])
            for row in rows
        }

    def list_applications(self, tenant_id: str) -> list[Application]:
        rows = self._conn.execute(
            "SELECT * FROM applications WHERE tenant_id = ? ORDER BY id", (tenant_id,)
        ).fetchall()
        return [
            Application(
                id=row["id"],
                tenant_id=row["tenant_id"],
                candidate_id=row["candidate_id"],
                job_id=row["job_id"],
                stage=ApplicationStage(row["stage"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def update_application_stage(
        self, tenant_id: str, application_id: str, stage: ApplicationStage
    ) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE applications SET stage = ? WHERE tenant_id = ? AND id = ?",
                (stage.value, tenant_id, application_id),
            )

    def add_audit_log(self, log: AuditLog) -> None:
        with self._conn:
            self._conn.execute(
                """INSERT INTO audit_logs
                   (id, tenant_id, application_id, from_stage, to_stage, actor_id, reason, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    log.id,
                    log.tenant_id,
                    log.application_id,
                    log.from_stage.value,
                    log.to_stage.value,
                    log.actor_id,
                    log.reason,
                    log.created_at,
                ),
            )

    def list_audit_logs(
        self, tenant_id: str, application_id: str | None = None
    ) -> list[AuditLog]:
        query = "SELECT * FROM audit_logs WHERE tenant_id = ?"
        params: list[object] = [tenant_id]
        if application_id is not None:
            query += " AND application_id = ?"
            params.append(application_id)
        query += " ORDER BY created_at, id"
        rows = self._conn.execute(query, params).fetchall()
        return [
            AuditLog(
                id=row["id"],
                tenant_id=row["tenant_id"],
                application_id=row["application_id"],
                from_stage=ApplicationStage(row["from_stage"]),
                to_stage=ApplicationStage(row["to_stage"]),
                actor_id=row["actor_id"],
                reason=row["reason"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def record_telemetry(self, event: TelemetryEvent) -> None:
        with self._conn:
            self._conn.execute(
                """INSERT INTO telemetry_events
                   (id, tenant_id, operation, provider, model, latency_ms, tokens_in,
                    tokens_out, citation_pass_rate, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    event.id,
                    event.tenant_id,
                    event.operation,
                    event.provider,
                    event.model,
                    event.latency_ms,
                    event.tokens_in,
                    event.tokens_out,
                    event.citation_pass_rate,
                    event.status,
                    event.created_at,
                ),
            )

    def list_telemetry(self, tenant_id: str) -> list[TelemetryEvent]:
        rows = self._conn.execute(
            "SELECT * FROM telemetry_events WHERE tenant_id = ? ORDER BY created_at, id",
            (tenant_id,),
        ).fetchall()
        return [
            TelemetryEvent(
                id=row["id"],
                tenant_id=row["tenant_id"],
                operation=row["operation"],
                provider=row["provider"],
                model=row["model"],
                latency_ms=float(row["latency_ms"]),
                tokens_in=int(row["tokens_in"]),
                tokens_out=int(row["tokens_out"]),
                citation_pass_rate=float(row["citation_pass_rate"]),
                status=row["status"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def close(self) -> None:
        self._conn.close()

    def __del__(self) -> None:
        connection = getattr(self, "_conn", None)
        if connection is not None:
            connection.close()
