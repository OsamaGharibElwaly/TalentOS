---

## File 2: `talentos/skills/phase-2/SKILL.md`
```markdown
---
name: talentos-phase-2
description: Days 4-6 Asynchronous Resume Ingestion, Deterministic Text Extraction, Schema-Validated Profile Parsing, and Local Hybrid Indexing for TalentOS.
---

# Phase 2: Resume Ingestion, Profile Parsing & Local Hybrid Indexing (Days 4–6)

## 1. Strict Execution Guardrails
- **NO AUTO-INSTALL:** Do NOT run `pip install`, `docker`, or download external models/services unless explicitly instructed. Use existing local libraries with deterministic stdlib fallbacks for `.txt`/`.md`/`.pdf`/`.docx` parsing.
- **Zero-API-Cost Default:** Implement `InferencePort` with a deterministic local/offline extractor + pluggable LLM adapter interface (disabled by default until configured).
- **Idempotency:** Deduplicate uploaded resumes per organization using SHA-256 file hashes.

## 2. Target Modules
```text
app/
├── ports/
│   ├── queue.py
│   ├── inference.py
│   └── vector_index.py
├── adapters/
│   ├── local_queue.py
│   ├── offline_extractor.py
│   └── local_hybrid_index.py
└── services/
    ├── document_parser.py
    └── ingestion_service.py
tests/
├── test_ingestion_pipeline.py
└── test_profile_schema.py
3. Deliverables & Implementation Specs
Multi-Format Document Text Extractor (document_parser.py):

Extract normalized text and section boundaries from .txt, .md, and (when local parsers exist) .pdf/.docx without crashing on malformed files.

Compute file_hash = sha256(raw_bytes) and store original file via StoragePort.

Strict Schema-Validated CandidateProfile:

Fields: full_name, email, phone, links, total_experience_years, skills (normalized lowercase tags), experience_entries (title, company, duration_months, highlights), education, raw_chunks.

Enforce bounded schema validation & repair loop (max 2 retries) before persisting.

Local Async Queue (LocalAsyncQueue):

Implement QueuePort (enqueue, process_next, get_job_status) tracking states: QUEUED -> PARSING -> INDEXED | FAILED.

Support batch ingestion of up to 50 files with per-file error isolation (one corrupt file never aborts the batch).

Local Hybrid Index (LocalHybridIndex):

Implement VectorIndexPort combining TF-IDF / token-overlap cosine similarity + metadata filtering stored locally in SQLite/JSON/NumPy without external vector DB servers.

4. Definition of Done (Verification Gate)
[ ] Batch ingestion test processes valid + malformed + duplicate resumes cleanly.

[ ] Re-uploading the same file hash within an org updates/links rather than duplicating candidate rows.

[ ] pytest tests/test_ingestion_pipeline.py tests/test_profile_schema.py passes 100%.