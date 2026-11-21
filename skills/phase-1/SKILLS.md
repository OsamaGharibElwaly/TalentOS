---
name: talentos-phase-1
description: Days 1-3 Foundation, Multi-Tenancy, RBAC, Job & Weighted Rubric Core, and Local Storage Ports for TalentOS.
---

# Phase 1: Foundation, Multi-Tenancy & Weighted Rubric Core (Days 1–3)

## 1. Strict Execution Guardrails
- **NO AUTO-INSTALL:** Do NOT install OS packages, Python libraries (`pip install`), Docker images, S3/MinIO, Postgres, Redis, or external LLM APIs unless explicitly instructed by the user.
- **Zero-Cost Local Defaults:** Use Python standard library + already-installed local packages, local SQLite persistence (`./data/talentos.db`), and local filesystem storage (`./data/storage/`).
- **Clean Architecture:** Isolate domain logic from infrastructure behind explicit Protocol/ABC ports (`StoragePort`, `RepositoryPort`).
- **Verification-First:** Every module must have strict static typing and passing `pytest` unit/integration tests before concluding the phase.

## 2. Target Directory Structure
```text
talentos/
├── .env.example
├── pyproject.toml
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── domain/
│   │   ├── models.py
│   │   ├── enums.py
│   │   └── exceptions.py
│   ├── ports/
│   │   ├── storage.py
│   │   └── repositories.py
│   ├── adapters/
│   │   ├── local_storage.py
│   │   └── sqlite_repo.py
│   ├── services/
│   │   ├── auth_service.py
│   │   └── job_service.py
│   └── api/
│       ├── main.py
│       ├── deps.py
│       └── routes_jobs.py
└── tests/
    ├── test_rbac_tenancy.py
    └── test_rubric_validation.py