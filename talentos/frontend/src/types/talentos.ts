export type UserRole = 'admin' | 'recruiter' | 'hiring_manager' | 'viewer';

export type Permission =
  | 'job:create'
  | 'job:read'
  | 'application:create'
  | 'application:read'
  | 'telemetry:read';

export type ApplicationStage =
  | 'NEW'
  | 'SCREENED'
  | 'SHORTLISTED'
  | 'INTERVIEW'
  | 'FINAL_REVIEW'
  | 'OFFER'
  | 'REJECTED';

export type IngestionStatus = 'QUEUED' | 'PARSING' | 'INDEXED' | 'FAILED';
export type HireRecommendation = 'STRONG_HIRE' | 'HIRE' | 'NEEDS_REVIEW' | 'NO_HIRE';

export interface Organization {
  readonly id: string;
  readonly name: string;
}

export interface Session {
  readonly user_id: string;
  readonly tenant_id: string;
  readonly role: UserRole;
  readonly permissions: readonly Permission[];
}

export interface Account {
  readonly user_id: string;
  readonly tenant_id: string;
  readonly role: UserRole;
  readonly organization: string;
  readonly full_name: string;
}

export interface RubricCriterion {
  id: string;
  name: string;
  weight: number;
  description: string;
  mandatory: boolean;
}

export interface Job {
  id: string;
  tenant_id: string;
  title: string;
  description: string;
  created_by: string;
  rubric: RubricCriterion[];
}

export interface ExperienceEntry {
  title: string;
  company: string;
  duration_months: number;
  highlights: string[];
}

export interface EducationEntry {
  school: string;
  degree: string;
  year: string;
}

export interface CandidateProfile {
  full_name: string;
  email: string;
  phone: string;
  links: string[];
  total_experience_years: number;
  skills: string[];
  experience_entries: ExperienceEntry[];
  education: EducationEntry[];
  raw_chunks: string[];
  raw_text: string;
}

export interface CitationEvidence {
  quote: string;
  verified: boolean;
  similarity: number;
}

export interface CriterionBreakdown {
  criterion_id: string;
  criterion_name: string;
  weight: number;
  score: number;
  rationale: string;
  citations: CitationEvidence[];
  confidence: number;
}

export interface GapProbe {
  kind: string;
  criterion_id: string;
  detail: string;
}

export interface ApplicationScore {
  application_id: string;
  candidate_id: string;
  composite_score: number;
  criterion_scores: CriterionBreakdown[];
  gaps_and_probes: GapProbe[];
  blind_mode: boolean;
}

export interface ApplicationSummary {
  id: string;
  job_id: string;
  stage: ApplicationStage;
  scoring: ApplicationScore | null;
}

export interface CandidateReview {
  candidate_id: string;
  full_name: string;
  email: string;
  phone: string;
  skills: string[];
  total_experience_years: number;
  raw_text: string;
  pii_masked: boolean;
  applications: ApplicationSummary[];
}

export interface Application {
  id: string;
  tenant_id: string;
  candidate_id: string;
  job_id: string;
  stage: ApplicationStage;
  created_at: string;
  full_name: string;
  email: string;
  phone: string;
}

export interface UploadStatus {
  filename: string;
  file_hash: string;
  status: IngestionStatus;
  duplicate: boolean;
  candidate_id: string | null;
  error: string;
}

export interface InterviewQuestion {
  text: string;
  target_criterion: string;
  resume_context: string;
  strong_signal_indicators: string[];
  red_flag_indicators: string[];
}

export interface CriterionRating {
  criterion_id: string;
  criterion_name: string;
  rating: number;
  evidence: string;
}

export interface ResumeDiscrepancy {
  claim: string;
  note: string;
  criterion_id: string;
}

export interface InterviewScorecard {
  candidate_id: string;
  job_id: string;
  criterion_ratings: CriterionRating[];
  strengths: string[];
  concerns: string[];
  resume_discrepancies: ResumeDiscrepancy[];
  hire_recommendation: HireRecommendation;
  raw_notes: string;
}

export interface TalentSearchResult {
  candidate_id: string;
  profile: CandidateProfile;
  score: number;
  highlighted_excerpt: string;
}

export interface InsightRank {
  label: string;
  value: number;
}

export interface InsightDecision {
  title: string;
  detail: string;
  href: string;
  tone: string;
}

export interface HiringInsights {
  tenant_id: string;
  candidates: number;
  applications: number;
  by_stage: Record<string, number>;
  average_score: number;
  scored_applications: number;
  top_skills: InsightRank[];
  ready_to_interview: InsightRank[];
  needs_review: number;
  decisions: InsightDecision[];
}

export interface TelemetrySummary {
  tenant_id: string;
  total_operations: number;
  success_count: number;
  failure_count: number;
  average_latency_ms: number;
  tokens_in: number;
  tokens_out: number;
  citation_pass_rate: number;
  by_operation: Record<string, number>;
}
