import type {
  Account,
  Application,
  ApplicationScore,
  ApplicationStage,
  HiringInsights,
  InterviewQuestion,
  InterviewScorecard,
  Job,
  CandidateReview,
  RubricCriterion,
  Session,
  TalentSearchResult,
  TelemetrySummary,
  UploadStatus,
} from '../types/talentos';
import { authHeaders, csrfHeaders, readSession } from './auth-session';
import { ApiError } from './errors';
import { cachedGet, invalidateCache } from './query-cache';

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? '';
const CACHE_TTL_MS = 30_000;

export interface JobCreatePayload {
  title: string;
  description: string;
  rubric: RubricCriterion[];
}

export interface AccountCreatePayload {
  organization: string;
  full_name: string;
  email: string;
}

export interface CriterionEvaluationInput {
  criterion_id: string;
  score: number;
  rationale: string;
  citations: string[];
  confidence: number;
}

export interface ScoreRequest {
  application_id: string;
  evaluations: CriterionEvaluationInput[];
  blind_mode: boolean;
}

export interface QuestionRequest {
  candidate_id: string;
  job_id: string;
  application_id: string | null;
}

export interface ScorecardRequest {
  candidate_id: string;
  job_id: string;
  raw_notes: string;
}

export interface TalentSearchPayload {
  query: string;
  min_experience_years: number | null;
  required_skills: string[];
  stage: ApplicationStage | null;
  top_k: number;
}

export interface TransitionPayload {
  to_stage: ApplicationStage;
  reason: string;
  confirm: boolean;
}

export interface ApplicationCreatePayload {
  candidate_id: string;
  job_id: string;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const mutating = init.method !== undefined && init.method !== 'GET';
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(readSession()),
      ...(mutating ? csrfHeaders() : {}),
      ...(init.headers ?? {}),
    },
  });
  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }
  return (await response.json()) as T;
}

async function mutate<T>(path: string, payload: unknown): Promise<T> {
  const result = await request<T>(path, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  invalidateCache('');
  return result;
}

export const api = {
  createAccount: (payload: AccountCreatePayload): Promise<Account> =>
    mutate<Account>('/frontend/account', payload),
  session: (): Promise<Session> =>
    cachedGet('/frontend/session', CACHE_TTL_MS, () => request<Session>('/frontend/session')),

  listJobs: (): Promise<Job[]> =>
    cachedGet('/frontend/jobs', CACHE_TTL_MS, () => request<Job[]>('/frontend/jobs')),
  getJob: (jobId: string): Promise<Job> =>
    cachedGet(`/frontend/jobs/${jobId}`, CACHE_TTL_MS, () =>
      request<Job>(`/frontend/jobs/${encodeURIComponent(jobId)}`)),
  createJob: (payload: JobCreatePayload): Promise<Job> =>
    mutate<Job>('/frontend/jobs', payload),

  listCandidates: (): Promise<CandidateReview[]> =>
    cachedGet('/frontend/candidates', CACHE_TTL_MS, () =>
      request<CandidateReview[]>('/frontend/candidates')),
  createApplication: (payload: ApplicationCreatePayload): Promise<Application> =>
    mutate<Application>('/applications', payload),
  getApplication: (applicationId: string): Promise<Application> =>
    cachedGet(`/applications/${applicationId}`, CACHE_TTL_MS, () =>
      request<Application>(`/applications/${encodeURIComponent(applicationId)}`)),
  transitionApplication: (applicationId: string, payload: TransitionPayload): Promise<Application> =>
    mutate<Application>(`/applications/${encodeURIComponent(applicationId)}/transition`, payload),
  scoreApplication: (payload: ScoreRequest): Promise<ApplicationScore> =>
    mutate<ApplicationScore>('/frontend/scoring', payload),

  ingestResumes: async (files: readonly File[]): Promise<UploadStatus[]> => {
    const form = new FormData();
    files.forEach((file) => form.append('files', file, file.name));
    const response = await fetch(`${API_BASE}/frontend/ingest`, {
      method: 'POST',
      headers: { ...authHeaders(readSession()), ...csrfHeaders() },
      body: form,
    });
    if (!response.ok) {
      throw new ApiError(response.status, await response.text());
    }
    invalidateCache('');
    return (await response.json()) as UploadStatus[];
  },

  generateQuestions: (payload: QuestionRequest): Promise<InterviewQuestion[]> =>
    mutate<InterviewQuestion[]>('/interviews/questions', payload),
  synthesizeScorecard: (payload: ScorecardRequest): Promise<InterviewScorecard> =>
    mutate<InterviewScorecard>('/interviews/scorecards', payload),

  searchTalent: (
    payload: TalentSearchPayload,
    signal?: AbortSignal,
  ): Promise<TalentSearchResult[]> =>
    request<TalentSearchResult[]>('/search/talent', {
      method: 'POST',
      body: JSON.stringify(payload),
      signal,
    }),

  insights: (): Promise<HiringInsights> =>
    cachedGet('/frontend/insights', CACHE_TTL_MS, () =>
      request<HiringInsights>('/frontend/insights')),

  telemetrySummary: (): Promise<TelemetrySummary> =>
    cachedGet('/api/v1/telemetry/summary', CACHE_TTL_MS, () =>
      request<TelemetrySummary>('/api/v1/telemetry/summary')),
};
