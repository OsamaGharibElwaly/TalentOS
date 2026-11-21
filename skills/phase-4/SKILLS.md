---

## File 4: `talentos/skills/phase-4/SKILL.md`
```markdown
---
name: talentos-phase-4
description: Days 10-12 AI Interview Copilot, Note-to-Scorecard Synthesizer, Talent Pool Hybrid Search, and Pipeline Stage Transitions for TalentOS.
---

# Phase 4: Interview Copilot, Scorecard Calibration & Talent Pool Search (Days 10–12)

## 1. Strict Execution Guardrails
- **NO AUTO-INSTALL:** Continue running 100% locally with zero unapproved installs or network dependencies.
- **Human Decision Authority:** Stage transitions (`REJECTED`, `OFFER`) require explicit user action and audit logging; AI may only recommend.

## 2. Target Modules
```text
app/
├── services/
│   ├── interview_copilot.py
│   ├── talent_search_service.py
│   └── pipeline_service.py
└── api/
    ├── routes_interviews.py
    └── routes_search.py
tests/
├── test_interview_copilot.py
└── test_talent_search.py
3. Deliverables & Implementation Specs
Tailored Interview Question Generator (interview_copilot.py):

Generates 5–8 role- and gap-specific questions mapped to rubric criteria, each including target_criterion, resume_context, strong_signal_indicators, and red_flag_indicators.

Note-to-Scorecard Synthesizer:

Converts raw interviewer notes/transcript text into a structured InterviewScorecard (criterion_ratings, strengths, concerns, resume_discrepancies, hire_recommendation), preserving raw notes untouched alongside the synthesis.

Talent Pool Hybrid Search (talent_search_service.py):

Accepts natural-language queries + optional structured filters (min_experience_years, required_skills, stage).

Combines SQL metadata filtering with LocalHybridIndex similarity ranking and returns matching candidate profiles with highlighted resume excerpts.

Audited Pipeline Stage Machine (pipeline_service.py):

Enforces valid stage transitions (NEW -> SCREENED -> SHORTLISTED -> INTERVIEW -> FINAL_REVIEW -> OFFER | REJECTED) and logs every transition in audit_logs.

4. Definition of Done (Verification Gate)
[ ] Question generator produces criterion-mapped questions grounded in candidate gaps.

[ ] Scorecard synthesizer flags discrepancies when interview notes contradict resume claims.

[ ] Hybrid search respects organization_id boundaries and filter constraints.