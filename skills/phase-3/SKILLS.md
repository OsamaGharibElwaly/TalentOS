---

## File 3: `talentos/skills/phase-3/SKILL.md`
```markdown
---
name: talentos-phase-3
description: Days 7-9 Weighted Rubric Scoring Engine, Deterministic Citation Verifier, Blind Screening Toggle, and Gap Detection for TalentOS.
---

# Phase 3: Rubric Scoring & Deterministic Citation Guardrails (Days 7–9)

## 1. Strict Execution Guardrails
- **NO AUTO-INSTALL:** No external libraries, containers, or paid API calls unless explicitly authorized.
- **Anti-Hallucination Law:** Never persist an AI-generated score justification unless its cited resume snippet passes deterministic source verification.

## 2. Target Modules
```text
app/
├── services/
│   ├── pii_redactor.py
│   ├── citation_verifier.py
│   └── scoring_service.py
└── api/
    └── routes_applications.py
tests/
├── test_citation_verifier.py
└── test_rubric_scoring.py
3. Deliverables & Implementation SpecsBlind Screening PII Redactor (pii_redactor.py):Optional blind_mode=True flag strips candidate name, email, phone, URLs, and graduation years before passing text to the scoring engine.Weighted Rubric Scoring Engine (scoring_service.py):Evaluates each RubricCriterion (score: 0..100, rationale, citations: list[str], confidence).Computes exact weighted composite score: $\sum (score_i \times weight_i / 100)$.Generates structured gaps_and_probes (missing mandatory criteria or unsubstantiated skill claims).Deterministic Citation Verifier (citation_verifier.py):Normalizes whitespace/case and verifies each cited quote against candidate.raw_text using exact substring check or normalized token-sequence overlap (>= 0.90).Any citation failing verification is flagged (verified=False) and stripped from trusted evidence; if all citations for a criterion fail, trigger bounded re-grounding or downgrade confidence.RBAC PII Masking on API Responses:When HIRING_MANAGER fetches an application not yet in SHORTLISTED/INTERVIEW stage, mask email and phone.4. Definition of Done (Verification Gate)[ ] Unit tests prove fabricated quotes are caught and rejected by citation_verifier.py.[ ] Composite scores match manual weighted math to 1e-4 precision.[ ] Blind mode strips PII tokens before scoring input construction.