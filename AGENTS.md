# AGENTS.md — TalentOS (Token-Hardened OpenCode Execution Contract)

## 1. Session & Token Budget Law (200k Session Ceiling)
- **Session Ceiling:** Operate strictly inside a **200,000-token session budget** with disciplined context distribution:
  - Keep active context lean (< 45k tokens per turn when possible).
  - Never dump full repositories, huge logs, or multi-file outputs when targeted slices or diffs suffice.
  - Summarize prior completed tool outputs briefly instead of re-quoting raw payloads.
- **HALT Protocol:** Immediately **HALT** and ask the user before proceeding if:
  1. A requirement is ambiguous or conflicts with existing code/contracts.
  2. A task requires installing OS packages, `pip` packages, Docker images/services (S3/MinIO, Postgres, Redis, Ollama), or paid/external APIs without explicit user authorization.
  3. A destructive change, schema break, or test regression occurs without a clear fix path.

## 2. Startup & Phase Skill Loading Rule (Every Prompt)
1. **First Prompt / Cold Start:** Read `README.md` in the project root first to ground on project context, layout, and adapters. If `README.md` does not exist yet, note its absence and create/update it only as scoped by the active phase.
2. **Every Prompt:** Read `/skills/phase-n/SKILLS.md` (matching the active `n` in `phase-n`) before editing code or running checks. Re-verify its constraints and Definition of Done on every turn.

## 3. OpenCode Plugins (`rtk` & `ponytail`) — Mandatory Every Turn
- **Every user prompt** must execute through the active OpenCode **`rtk`** and **`ponytail`** plugin workflows:
  - Use `rtk` for token-compressed command/output handling and concise execution telemetry.
  - Use `ponytail` for structured task/step progression, guardrail checks, and clean handoffs.
  - If either plugin is unavailable or errors, **HALT** and report the exact blocker rather than silently bypassing guardrails.

## 4. Local-First, Zero-API-Cost & No-Auto-Install Rules
- Default to local-first, zero-cost execution (`./data/`, local adapters, deterministic checks).
- **Zero unapproved installations:** Never run `pip install`, `npm install`, `apt`/`winget`/`choco`, `docker pull`/`up`, or external service setup unless explicitly instructed in the prompt.

## 5. Modularity, Verification & Testing Protocol
- Keep changes modular with strict type annotations, clean boundaries, and minimal comments (only non-obvious invariants or why-not context).
- **Verification & Testing Loop:** Before reporting a phase/task complete:
  1. Run targeted static checks / type checks and `pytest` on relevant test files (via `rtk` compact output).
  2. Confirm every item in `/skills/phase-n/SKILLS.md` Definition of Done is satisfied.
  3. Output a concise summary: what changed, tests run & pass/fail status, token/context status, and next `HALT` or next step.