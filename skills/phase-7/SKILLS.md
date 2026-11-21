---

## File 2: `talentos/skills/phase-7/SKILLS.md`
*(Phase Title: **phase-7: Next.js Frontend-First Speed, Elegance & Full Security + Backend Optimization & Hardening**)*

```markdown
---
name: talentos-phase-7
description: Phase 7 Full Security & Performance Optimization for TalentOS — Next.js Frontend Speed, Visual Elegance & Full Browser Security first, followed by Backend Query/Async Throughput, Caching & API Security Hardening.
---

# Phase 7: Next.js Frontend-First Speed, Elegance & Full Security + Backend Hardening

## 1. Strict Execution Guardrails
- **Mandatory Execution Order:** Complete and verify **Part A (Next.js Frontend Speed, Elegance & Full Security)** first, then execute **Part B (Backend Speed & Full Security Hardening)**.
- **NO AUTO-INSTALL:** Do NOT run `npm install`, `pip install`, `docker`, or external service setup unless explicitly instructed by the user. Use native Next.js/React/Web APIs, standard Python libraries, SQLite optimizations, and existing dependencies.
- **Plugin & Budget Discipline:** Run via `rtk` and `ponytail` within the 200k-token session ceiling; **HALT** before changing public API schemas or before any unapproved install.

## 2. Target Files & Tests
```text
talentos/
├── frontend/
│   ├── next.config.ts
│   └── src/
│       ├── lib/
│       │   ├── security.ts
│       │   ├── api-client.ts
│       │   └── query-cache.ts
│       ├── components/
│       │   ├── ui/
│       │   │   ├── Skeletons.tsx
│       │   │   ├── SafeText.tsx
│       │   │   └── CommandPalette.tsx
│       │   └── candidates/
│       │       └── SplitEvidenceViewer.tsx
│       └── app/
│           └── globals.css
├── app/
│   ├── middleware/
│   │   ├── security_headers.py
│   │   └── rate_limiter.py
│   ├── adapters/
│   │   └── sqlite_repo.py
│   └── services/
│       └── scoring_service.py
└── tests/
    ├── test_frontend_security_perf.py
    └── test_backend_perf_hardening.py
3. Part A: Next.js Frontend Speed, Elegance & Full Security (Execute First)
Full Next.js Frontend Security (security.ts, next.config.ts, SafeText.tsx):

XSS & Injection Defense: Never use dangerouslySetInnerHTML with untrusted resume text, citations, candidate names, or interviewer notes. Render user/resume content via safe text nodes (SafeText.tsx) and explicit React JSX.

URL & Protocol Allowlisting: Validate all external links (sanitizeExternalUrl) to allow only https: and http: schemes (explicitly blocking javascript:, data:, vbscript:, and malformed URLs).

CSRF & Token Hygiene: Attach anti-CSRF/state-change headers (X-Requested-With / CSRF token) on mutating requests, avoid storing sensitive tokens in unguarded global state, and enforce rel="noopener noreferrer" on external links.

Next.js Security Headers (next.config.ts): Configure Content-Security-Policy (strict script/style/connect/img/frame-ancestors directives), X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Referrer-Policy: strict-origin-when-cross-origin, and Permissions-Policy.

Frontend Speed Enhancements (api-client.ts, query-cache.ts, Skeletons.tsx):

Deduplication, TTL Cache & Cancellation: Deduplicate concurrent identical GET requests, cache responses with configurable TTL + tag/prefix invalidation on mutations, debounce search inputs (250ms), and cancel stale in-flight requests via AbortController.

Rendering Performance: Use React.memo / useMemo / useCallback on heavy lists and split-pane evidence views, pagination/windowing for large candidate sets, and skeleton loaders (Skeletons.tsx) to prevent layout shift (CLS).

Visual Elegance & UX Enhancements (globals.css, CommandPalette.tsx):

Cohesive design tokens (spacing scale, surface elevation, semantic status badges, accessible focus-visible rings, keyboard shortcuts such as Cmd/Ctrl+K quick jump and Esc modal/drawer close, and prefers-reduced-motion support).

4. Part B: Backend Speed & Full Security Hardening (Execute Second)
Backend Speed & Query Optimization (sqlite_repo.py, scoring_service.py):

Add composite indexes ((organization_id, job_id, total_score), (organization_id, stage), (organization_id, file_hash)), enable SQLite WAL mode, synchronous=NORMAL, busy_timeout, and eliminate N+1 queries on list endpoints.

Add bounded caching for job rubrics and pre-compiled matching/redaction patterns.

Backend API & Data Security Hardening (security_headers.py, rate_limiter.py, validation):

Enforce HTTP security headers (Content-Security-Policy, X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Referrer-Policy, Cache-Control: no-store on auth/sensitive responses).

Enforce sliding-window rate limiting on upload, scoring, search, and auth endpoints, strict file size + extension + magic-byte checks, and path-traversal guards.

5. Definition of Done (Verification Gate)
[ ] Part A Verified First: pytest tests/test_frontend_security_perf.py passes (validates next.config.ts CSP/security headers, sanitizeExternalUrl blocking javascript:/data:, absence of unsafe dangerouslySetInnerHTML on untrusted fields, and cache/debounce/abort logic).

[ ] Part B Verified Second: pytest tests/test_backend_perf_hardening.py passes (validates indexed query performance on 200+ seeded rows, rate-limiter throttling, upload validation, and security headers).

[ ] Full pytest suite across Phases 1–7 passes with zero unapproved package or infrastructure installations.