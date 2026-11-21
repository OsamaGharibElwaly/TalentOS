from __future__ import annotations

import json
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from app.adapters.offline_extractor import OfflineExtractor
from app.adapters.sqlite_repo import SQLiteRepository
from app.domain.enums import ApplicationStage
from app.domain.exceptions import ProfileValidationError
from app.domain.models import Application, CriterionEvaluation, Job, RubricCriterion
from app.services.citation_verifier import CitationVerifier
from app.services.pii_redactor import PIIRedactor
from app.services.scoring_service import ScoringService
from app.services.telemetry_service import TelemetryService

FIXTURES = Path(__file__).parent / "fixtures" / "golden_resumes.json"
PROJECT_ROOT = Path(__file__).parent.parent
MIN_CITATION_PASS_RATE = 0.95


def lint_docker() -> list[str]:
    """Validate the blueprint's syntax and gating without building or starting anything."""
    errors: list[str] = []
    dockerfile = PROJECT_ROOT / "Dockerfile"
    compose = PROJECT_ROOT / "docker-compose.yml"

    if not dockerfile.is_file():
        errors.append("Dockerfile is missing")
    else:
        lines = [
            line.strip()
            for line in dockerfile.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        from_lines = [line for line in lines if line.upper().startswith("FROM ")]
        if len(from_lines) < 2:
            errors.append("Dockerfile must be multi-stage")
        if not any(" AS " in line.upper() for line in from_lines):
            errors.append("Dockerfile builder stage must be named with AS")
        if not any(line.upper().startswith(("CMD ", "ENTRYPOINT ")) for line in lines):
            errors.append("Dockerfile needs CMD or ENTRYPOINT")

    if not compose.is_file():
        errors.append("docker-compose.yml is missing")
        return errors
    try:
        import yaml

        document = yaml.safe_load(compose.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"docker-compose.yml is invalid YAML: {exc}")
        return errors

    if not isinstance(document, dict) or not isinstance(document.get("services"), dict):
        errors.append("docker-compose.yml must define a services mapping")
        return errors
    services = document["services"]
    if "app" not in services:
        errors.append("docker-compose.yml must define an app service")
    elif services["app"].get("profiles"):
        errors.append("app service must start in the default profile")
    for name, spec in services.items():
        if name != "app" and isinstance(spec, dict) and not spec.get("profiles"):
            errors.append(f"infra service '{name}' must be gated behind a profile")
    return errors


def main() -> int:
    errors: list[str] = []
    try:
        fixture = json.loads(FIXTURES.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print("RESULT: FAIL")
        print(f"fixture error: {exc}")
        return 1

    criteria = [RubricCriterion(**item) for item in fixture["rubric"]["criteria"]]
    job = Job(
        id=str(fixture["rubric"]["id"]),
        tenant_id="eval",
        title=str(fixture["rubric"]["title"]),
        rubric=criteria,
        created_by="evals",
    )
    extractor = OfflineExtractor()
    verifier = CitationVerifier()
    valid = 0
    citations_total = 0
    citations_verified = 0
    composites: dict[str, list[float]] = {}
    telemetry_count = 0

    with TemporaryDirectory() as temporary:
        repo = SQLiteRepository(Path(temporary) / "evals.db")
        telemetry = TelemetryService(repo)
        scorer = ScoringService(verifier, PIIRedactor(), repo)
        for item in fixture["cases"]:
            text = str(item["resume_text"])
            try:
                profile = extractor.extract_profile(text, [text])
            except ProfileValidationError as exc:
                errors.append(f"{item['id']}: schema invalid: {exc}")
                continue
            valid += 1
            evaluations = [CriterionEvaluation(**entry) for entry in item["evaluations"]]
            application = Application(
                id=str(item["id"]),
                tenant_id="eval",
                candidate_id=str(item["id"]),
                job_id=job.id,
                stage=ApplicationStage.NEW,
                created_at="2026-01-01T00:00:00+00:00",
            )
            started = time.perf_counter()
            result = scorer.score(
                application=application,
                candidate=profile,
                job=job,
                evaluations=evaluations,
            )
            latency = (time.perf_counter() - started) * 1000
            submitted = sum(len(evaluation.citations) for evaluation in evaluations)
            accepted = sum(len(score.citations) for score in result.criterion_scores)
            citations_total += submitted
            citations_verified += accepted
            telemetry.track(
                tenant_id="eval",
                operation="score_resume",
                latency_ms=latency,
                tokens_in=len(text) // 4,
                tokens_out=sum(len(score.rationale) for score in result.criterion_scores) // 4,
                citation_pass_rate=accepted / submitted if submitted else 0.0,
                status="ok",
            )
            telemetry_count += 1
            composites.setdefault(str(item["label"]), []).append(
                round(result.composite_score, 6)
            )
        summary = telemetry.summary("eval")
        repo.close()

    total_cases = len(fixture["cases"])
    schema_rate = valid / total_cases if total_cases else 0.0
    if schema_rate != 1.0:
        errors.append("schema validity is below 100%")
    pass_rate = citations_verified / citations_total if citations_total else 0.0
    if pass_rate < MIN_CITATION_PASS_RATE:
        errors.append("citation verification pass rate is below 95%")
    strong = composites.get("strong", [])
    partial = composites.get("partial", [])
    mismatch = composites.get("mismatch", [])
    ordering_ok = bool(
        strong and partial and mismatch and min(strong) > partial[0] > mismatch[0]
    )
    if not ordering_ok:
        errors.append("rank ordering regressed")
    docker_errors = lint_docker()
    errors.extend(docker_errors)

    print("TalentOS golden-set evaluation")
    print(f"cases: {total_cases}")
    print(f"schema_validity: {schema_rate:.2%} ({valid}/{total_cases})")
    print(f"citation_pass_rate: {pass_rate:.2%} ({citations_verified}/{citations_total})")
    print(
        f"rank_order: {'PASS' if ordering_ok else 'FAIL'} "
        f"strong={min(strong) if strong else 0.0:.4f} "
        f"partial={partial[0] if partial else 0.0:.4f} "
        f"mismatch={mismatch[0] if mismatch else 0.0:.4f}"
    )
    print(f"avg_latency_ms: {summary.average_latency_ms:.3f}")
    print(f"tokens_in: {summary.tokens_in}; tokens_out: {summary.tokens_out}")
    print(f"telemetry_events: {telemetry_count}")
    print(f"docker_lint: {'PASS' if not docker_errors else 'FAIL'}")
    if errors:
        print("RESULT: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("RESULT: FAIL")
        print(f"unexpected error: {exc}")
        raise SystemExit(1)
