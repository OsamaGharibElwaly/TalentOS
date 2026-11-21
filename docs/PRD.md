# TalentOS — Product Requirements Document (Stage 1)

> This file preserves the original phase contract and the Stage 1 product baseline.
> The repository landing page is now [`README.md`](../README.md).

## 1. Product intent

TalentOS is a local-first hiring workspace for recruiters and hiring teams. It keeps roles, resumes, candidate reviews, interviews, talent search and hiring activity in one calm interface. A recruiter can move from a job description to a defensible decision without learning a technical system or depending on an outside AI service.

## 2. Original phase 1 foundation

Source lives in `talentos/`. Phase rules: `skills/phase-1/SKILLS.md`.

Layout:

```text
talentos/
├── app/
│   ├── config.py            # env-driven settings (stdlib only)
│   ├── domain/              # models, enums, exceptions (framework-free)
│   ├── ports/               # StoragePort, RepositoryPort protocols
│   ├── adapters/            # LocalStorage, SQLiteRepository
│   ├── services/            # AuthService (RBAC/tenancy), JobService (rubric core)
│   └── api/                 # FastAPI app, dependencies, job routes
└── tests/
    ├── test_rbac_tenancy.py
    └── test_rubric_validation.py
```

Run locally:

```bash
cd talentos
python -m pytest
python -m uvicorn app.api.main:app --reload
```

All state is local: SQLite at `./data/talentos.db`, files at `./data/storage/`.
Copy `.env.example` to `.env` to override paths. No packages, Docker, or external
APIs are installed or required beyond what is already in the environment.

API identity: requests carry `X-User-Id` and `X-Tenant-Id` headers. RBAC and tenant isolation are enforced in the service layer before any repository call.

## 3. Phases 2–7

Ingestion/hybrid indexing, rubric scoring with citation guardrails, interview/search/pipeline services, telemetry/evaluation, Next.js frontend security and performance, and backend hardening are implemented in `talentos/`.

## 4. Stage 1 acceptance criteria

| Area | Requirement | Stage 1 status |
| --- | --- | --- |
| Frontend | All workspaces render HR-readable screens with SVG icons, visible loading, error/404 pages and route transitions | Done |
| Onboarding | Sign in to demo roles and create a fresh local workspace without granting admin | Done |
| Developer Mode | Every feature page ends with a guided JSON recipe for that process | Done |
| Backend | Tenant-safe endpoints, RBAC, rate limits, security headers, indexed SQLite | Done |
| AI | Offline resume parsing, weighted scoring, citation guardrails, copilot and hybrid search | Done |
| Verification | `pytest` and `tsc --noEmit` pass; live browser checks show no console errors | Done |

## 5. Out of scope for Stage 1

- Password-based authentication and external identity providers.
- Cloud deployment, containers or paid model APIs.
- Cross-tenant data sharing.
- Stage 2 productised admin onboarding and analytics.
