---

## File 5: `talentos/skills/phase-5/SKILL.md`
```markdown
---
name: talentos-phase-5
description: Days 13-15 Telemetry Observability, Golden-Set Evaluation Harness, Docker Compose Blueprint (Unexecuted), and Documentation for TalentOS.
---

# Phase 5: Telemetry, Golden Evaluation Suite & Docker Readiness (Days 13–15)

## 1. Strict Execution Guardrails
- **NO AUTO-INSTALL / NO AUTO-UP:** Write `Dockerfile` and `docker-compose.yml` as clean, ready-to-use templates, but **do NOT execute `docker build` or `docker compose up`** unless the user explicitly commands it.

## 2. Target Deliverables
```text
talentos/
├── Dockerfile
├── docker-compose.yml
├── app/
│   └── services/
│       └── telemetry_service.py
├── evals/
│   ├── fixtures/
│   │   └── golden_resumes.json
│   └── run_evals.py
└── README.md
3. Deliverables & Implementation Specs
AI & System Telemetry (telemetry_service.py):

Persist operation metrics (operation, provider, model, latency_ms, tokens_in, tokens_out, citation_pass_rate, status) and expose an Admin summary endpoint (GET /api/v1/telemetry/summary).

Automated Golden-Set Evaluation Harness (evals/run_evals.py):

Run automated benchmarks across synthetic/anonymized resumes and job rubrics asserting:

100% schema validity.

>= 95% citation verification pass rate.

Expected rank ordering between strong, partial, and mismatch candidate profiles.

Deterministic latency and exit code 0 on pass / 1 on regression.

Docker Blueprint (Ready on Command):

Dockerfile (multi-stage slim Python image) + docker-compose.yml with profiles (default local-mode app + optional infra profile for Postgres/pgvector, Redis, MinIO commented/gated so nothing starts unasked).

Architecture & Runbook README.md:

Document local startup, adapter swap flags, RBAC matrix, evaluation benchmark results, and system architecture diagram.

4. Definition of Done (Verification Gate)
[ ] python -m evals.run_evals exits 0 and prints reproducible benchmark metrics.

[ ] Full pytest suite passes with zero warnings/errors.

[ ] Dockerfile and docker-compose.yml lint cleanly without executing container builds.