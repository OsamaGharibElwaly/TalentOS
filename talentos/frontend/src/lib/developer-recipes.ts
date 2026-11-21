import type { DeveloperRecipe } from '../components/ui/DeveloperMode';

export type DeveloperRecipeKey =
  | 'overview'
  | 'guide'
  | 'jobs'
  | 'ingestion'
  | 'candidates'
  | 'interviews'
  | 'talentPool'
  | 'telemetry'
  | 'login';

export const DEVELOPER_RECIPES: Readonly<Record<DeveloperRecipeKey, DeveloperRecipe>> = {
  overview: {
    process: 'Open the hiring overview',
    steps: [
      { method: 'GET', path: '/frontend/session' },
      { method: 'GET', path: '/frontend/jobs' },
      { method: 'GET', path: '/frontend/candidates' },
      { method: 'GET', path: '/frontend/insights' },
    ],
  },
  guide: {
    process: 'Follow one hire from planning to decision',
    steps: [
      { method: 'VIEW', path: '/jobs' },
      { method: 'VIEW', path: '/ingestion' },
      { method: 'VIEW', path: '/candidates' },
      { method: 'VIEW', path: '/interviews' },
      { method: 'VIEW', path: '/talent-pool' },
      { method: 'VIEW', path: '/telemetry' },
    ],
  },
  jobs: {
    process: 'Create a role and its weighted scorecard',
    steps: [
      { method: 'GET', path: '/frontend/jobs' },
      {
        method: 'POST',
        path: '/jobs',
        body: {
          title: 'Senior Backend Engineer',
          description: 'Owns Python services and the SQL data model.',
          rubric: [
            {
              id: 'python',
              name: 'Python engineering',
              weight: 0.6,
              description: 'Builds reliable backend services.',
              mandatory: true,
            },
            {
              id: 'sql',
              name: 'SQL and data design',
              weight: 0.4,
              description: 'Designs clear schemas and queries.',
              mandatory: false,
            },
          ],
        },
      },
    ],
  },
  ingestion: {
    process: 'Add resumes and skip duplicates',
    steps: [
      {
        method: 'POST',
        path: '/frontend/ingest',
        body: {
          multipart: {
            files: [
              { filename: 'alex-morgan.txt', content_type: 'text/plain', duplicate_check: 'sha256' },
              { filename: 'sam-lee.txt', content_type: 'text/plain', duplicate_check: 'sha256' },
            ],
          },
        },
      },
      { method: 'GET', path: '/frontend/candidates' },
    ],
  },
  candidates: {
    process: 'Review candidates against the role',
    steps: [
      { method: 'GET', path: '/frontend/candidates' },
      {
        method: 'POST',
        path: '/frontend/scoring',
        body: {
          application_id: 'app-1',
          blind_mode: true,
          evaluations: [
            {
              criterion_id: 'python',
              score: 4,
              rationale: 'Built services with Python.',
              citations: ['Built services with Python'],
              confidence: 0.9,
            },
          ],
        },
      },
    ],
  },
  interviews: {
    process: 'Prepare questions and capture interview notes',
    steps: [
      {
        method: 'POST',
        path: '/interviews/questions',
        body: {
          candidate_id: 'cand-1',
          job_id: 'job-1',
          application_id: 'app-1',
        },
      },
      {
        method: 'POST',
        path: '/interviews/scorecards',
        body: {
          candidate_id: 'cand-1',
          job_id: 'job-1',
          raw_notes: 'Clear examples of backend ownership and careful SQL design.',
        },
      },
    ],
  },
  talentPool: {
    process: 'Search the talent pool by skill and stage',
    steps: [
      {
        method: 'POST',
        path: '/search/talent',
        body: {
          query: 'python sql',
          min_experience_years: 5,
          required_skills: ['python', 'sql'],
          stage: 'SHORTLISTED',
          top_k: 5,
        },
      },
    ],
  },
  telemetry: {
    process: 'Read hiring activity and next steps',
    steps: [
      { method: 'GET', path: '/frontend/insights' },
      { method: 'GET', path: '/api/v1/telemetry/summary' },
    ],
  },
  login: {
    process: 'Open an existing workspace or create a new one',
    steps: [
      {
        method: 'POST',
        path: '/frontend/account',
        body: {
          organization: 'Northstar Hiring',
          full_name: 'Alex Morgan',
          email: 'alex@northstar.example',
        },
      },
      { method: 'GET', path: '/frontend/session' },
    ],
  },
};
