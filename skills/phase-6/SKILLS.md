Markdown
---
name: talentos-phase-6
description: Phase 6 Unified Next.js Frontend wrapping all TalentOS HR/ATS workflows (Auth/RBAC, Job & Weighted Rubric Builder, Bulk Resume Ingestion, Evidence-Cited Candidate Review, Interview Copilot, Talent Pool Search, and Telemetry Dashboard).
---

# Phase 6: Next.js Unified Frontend Wrapping All TalentOS Workflows

## 1. Strict Execution Guardrails
- **NO AUTO-INSTALL:** Do NOT run `npm install`, `pnpm install`, `yarn add`, `pip install`, `docker`, or download external packages/services unless explicitly instructed by the user.
- **Inspect Before Scaffolding:** Check if a Next.js app, `package.json`, or `node_modules` already exists in the repo. If Next.js files/dependencies are already present locally, build directly inside them; if `node_modules` or Next.js dependencies are missing, author the complete Next.js source files (`app/`, `components/`, `lib/`, `types/`, `next.config.*`) cleanly and **HALT** before running any unapproved package install or build command.
- **Plugin & Budget Discipline:** Operate through `rtk` and `ponytail` within our 200k-token session ceiling; **HALT** if any API contract is missing or ambiguous.

## 2. Target Next.js Directory Structure
```text
talentos/
├── frontend/
│   ├── next.config.ts
│   ├── tsconfig.json
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── globals.css
│   │   │   ├── jobs/
│   │   │   │   └── page.tsx
│   │   │   ├── ingestion/
│   │   │   │   └── page.tsx
│   │   │   ├── candidates/
│   │   │   │   └── page.tsx
│   │   │   ├── interviews/
│   │   │   │   └── page.tsx
│   │   │   ├── talent-pool/
│   │   │   │   └── page.tsx
│   │   │   └── telemetry/
│   │   │       └── page.tsx
│   │   ├── components/
│   │   │   ├── shell/
│   │   │   │   ├── AppShell.tsx
│   │   │   │   ├── SidebarNav.tsx
│   │   │   │   └── WorkspaceRbacBar.tsx
│   │   │   ├── jobs/
│   │   │   │   └── RubricWeightEditor.tsx
│   │   │   ├── ingestion/
│   │   │   │   └── BulkResumeDropzone.tsx
│   │   │   ├── candidates/
│   │   │   │   └── SplitEvidenceViewer.tsx
│   │   │   ├── interviews/
│   │   │   │   └── InterviewCopilotPanel.tsx
│   │   │   ├── search/
│   │   │   │   └── TalentSearchWorkbench.tsx
│   │   │   └── telemetry/
│   │   │       └── TelemetryMetricsGrid.tsx
│   │   ├── lib/
│   │   │   ├── api-client.ts
│   │   │   ├── auth-session.ts
│   │   │   └── security.ts
│   │   └── types/
│   │       └── talentos.ts
├── app/
│   └── api/
│       └── routes_frontend.py
└── tests/
    └── test_frontend_contract.py
3. Deliverables & Implementation Specs
Strict TypeScript Domain Contracts (types/talentos.ts):

Strongly typed interfaces for Organization, UserRole (ADMIN, RECRUITER, HIRING_MANAGER), Job, RubricCriterion, CandidateProfile, ApplicationScore, CitationEvidence, InterviewScorecard, and TelemetrySummary.

RBAC-Aware App Shell & Workspace Switcher (AppShell.tsx, SidebarNav.tsx, WorkspaceRbacBar.tsx):

Multi-tenant workspace context + role switching/session state.

Enforces UI route/action visibility per role: HIRING_MANAGER sees masked PII before SHORTLISTED and cannot edit global rubrics or view admin telemetry; RECRUITER manages jobs, ingestion, and talent pool; ADMIN accesses full workspace & telemetry views.

Job & Weighted Rubric Builder (jobs/page.tsx, RubricWeightEditor.tsx):

Create/edit requisitions and criterion weights with live validation requiring exact 100% weight allocation before submit.

Bulk Resume Ingestion Queue (ingestion/page.tsx, BulkResumeDropzone.tsx):

Multi-file upload (PDF, DOCX, TXT, MD) with status tracking (QUEUED -> PARSING -> INDEXED | FAILED), duplicate SHA-256 feedback, and isolated error reporting.

Split-Screen Evidence-Cited Candidate Review (candidates/page.tsx, SplitEvidenceViewer.tsx):

Left pane displays extracted resume text with highlighted evidence passages; right pane displays weighted composite score, per-criterion breakdowns, verified vs. unverified citation badges, skill gaps, Blind Screening mode toggle, and pipeline stage actions.

Interview Copilot, Talent Pool Search & Telemetry (interviews/page.tsx, talent-pool/page.tsx, telemetry/page.tsx):

Tailored interview questions + evaluation anchors + raw-notes-to-scorecard synthesis.

Hybrid talent search with skill/experience/stage filters and evidence excerpts.

Telemetry dashboard displaying funnel counts, token/latency metrics, and citation verification pass rates.

4. Definition of Done (Verification Gate)
[ ] All Next.js pages and components cover every backend capability from phase-1 through phase-5 with strict TypeScript types.

[ ] RBAC visibility and PII masking rules in the UI match backend enforcement.

[ ] pytest tests/test_frontend_contract.py passes (verifying Next.js route/component structure, API client payload contracts, and security helpers without installing packages).

[ ] Zero unapproved npm install, pip install, or infrastructure commands executed.