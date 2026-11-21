from dataclasses import dataclass, field

from app.domain.enums import ApplicationStage, HireRecommendation, IngestionStatus, Role


@dataclass(frozen=True, slots=True)
class Tenant:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class User:
    id: str
    tenant_id: str
    role: Role
    email: str = ""


@dataclass(frozen=True, slots=True)
class RubricCriterion:
    id: str
    name: str
    weight: float
    description: str = ""
    mandatory: bool = False


@dataclass(slots=True)
class Job:
    id: str
    tenant_id: str
    title: str
    rubric: list[RubricCriterion]
    created_by: str
    description: str = ""


@dataclass(frozen=True, slots=True)
class ExperienceEntry:
    title: str
    company: str
    duration_months: int
    highlights: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class EducationEntry:
    school: str
    degree: str = ""
    year: str = ""


@dataclass(frozen=True, slots=True)
class CandidateProfile:
    full_name: str
    email: str
    phone: str
    links: list[str]
    total_experience_years: float
    skills: list[str]
    experience_entries: list[ExperienceEntry]
    education: list[EducationEntry]
    raw_chunks: list[str]
    raw_text: str = ""


@dataclass(slots=True)
class CandidateRecord:
    id: str
    tenant_id: str
    file_hash: str
    filename: str
    storage_key: str
    profile: CandidateProfile
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    filename: str
    file_hash: str
    storage_key: str
    text: str
    chunks: list[str]


@dataclass(frozen=True, slots=True)
class DocumentUpload:
    filename: str
    raw_bytes: bytes


@dataclass(slots=True)
class QueuedJob:
    id: str
    tenant_id: str
    upload: DocumentUpload
    status: IngestionStatus
    error: str = ""


@dataclass(frozen=True, slots=True)
class SearchHit:
    doc_id: str
    score: float
    metadata: dict[str, object]


@dataclass(slots=True)
class Application:
    id: str
    tenant_id: str
    candidate_id: str
    job_id: str
    stage: ApplicationStage
    created_at: str


@dataclass(frozen=True, slots=True)
class CriterionEvaluation:
    criterion_id: str
    score: int
    rationale: str
    citations: list[str]
    confidence: float = 1.0


@dataclass(frozen=True, slots=True)
class Citation:
    quote: str
    verified: bool
    similarity: float


@dataclass(frozen=True, slots=True)
class CriterionScore:
    criterion_id: str
    criterion_name: str
    weight: float
    score: int
    rationale: str
    citations: list[Citation]
    confidence: float


@dataclass(frozen=True, slots=True)
class GapProbe:
    kind: str
    criterion_id: str
    detail: str


@dataclass(frozen=True, slots=True)
class ScoringResult:
    application_id: str
    candidate_id: str
    composite_score: float
    criterion_scores: list[CriterionScore]
    gaps_and_probes: list[GapProbe]
    blind_mode: bool


@dataclass(frozen=True, slots=True)
class InterviewQuestion:
    text: str
    target_criterion: str
    resume_context: str
    strong_signal_indicators: list[str]
    red_flag_indicators: list[str]


@dataclass(frozen=True, slots=True)
class CriterionRating:
    criterion_id: str
    criterion_name: str
    rating: int
    evidence: str


@dataclass(frozen=True, slots=True)
class ResumeDiscrepancy:
    claim: str
    note: str
    criterion_id: str = "profile"


@dataclass(frozen=True, slots=True)
class InterviewScorecard:
    candidate_id: str
    job_id: str
    criterion_ratings: list[CriterionRating]
    strengths: list[str]
    concerns: list[str]
    resume_discrepancies: list[ResumeDiscrepancy]
    hire_recommendation: HireRecommendation
    raw_notes: str


@dataclass(frozen=True, slots=True)
class AuditLog:
    id: str
    tenant_id: str
    application_id: str
    from_stage: ApplicationStage
    to_stage: ApplicationStage
    actor_id: str
    reason: str
    created_at: str


@dataclass(frozen=True, slots=True)
class StageRecommendation:
    application_id: str
    from_stage: ApplicationStage
    to_stage: ApplicationStage
    rationale: str
    requires_human_confirmation: bool


@dataclass(frozen=True, slots=True)
class TalentSearchResult:
    candidate_id: str
    profile: CandidateProfile
    score: float
    highlighted_excerpt: str


@dataclass(frozen=True, slots=True)
class TelemetryEvent:
    id: str
    tenant_id: str
    operation: str
    provider: str
    model: str
    latency_ms: float
    tokens_in: int
    tokens_out: int
    citation_pass_rate: float
    status: str
    created_at: str


@dataclass(frozen=True, slots=True)
class TelemetrySummary:
    tenant_id: str
    total_operations: int
    success_count: int
    failure_count: int
    average_latency_ms: float
    tokens_in: int
    tokens_out: int
    citation_pass_rate: float
    by_operation: dict[str, int]


@dataclass(frozen=True, slots=True)
class InsightRank:
    label: str
    value: float


@dataclass(frozen=True, slots=True)
class InsightDecision:
    title: str
    detail: str
    href: str
    tone: str


@dataclass(frozen=True, slots=True)
class HiringInsights:
    tenant_id: str
    candidates: int
    applications: int
    by_stage: dict[str, int]
    average_score: float
    scored_applications: int
    top_skills: list[InsightRank]
    ready_to_interview: list[InsightRank]
    needs_review: int
    decisions: list[InsightDecision]
