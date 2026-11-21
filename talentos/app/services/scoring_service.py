from __future__ import annotations

from functools import lru_cache

from app.domain.models import (
    Application,
    CandidateProfile,
    CriterionEvaluation,
    CriterionScore,
    GapProbe,
    Job,
    RubricCriterion,
    ScoringResult,
)
from app.ports.repositories import RepositoryPort
from app.services.citation_verifier import CitationVerifier, normalize
from app.services.pii_redactor import PIIRedactor

MAX_SCORE = 100
FULL_REJECTION_FACTOR = 0.25
PARTIAL_REJECTION_FACTOR = 0.75


@lru_cache(maxsize=128)
def _criteria_index(criteria: tuple[RubricCriterion, ...]) -> dict[str, RubricCriterion]:
    return {criterion.id: criterion for criterion in criteria}


class ScoringService:
    """Weighted rubric scoring with deterministic citation guardrails."""

    def __init__(
        self,
        verifier: CitationVerifier,
        redactor: PIIRedactor,
        repo: RepositoryPort,
    ) -> None:
        self._verifier = verifier
        self._redactor = redactor
        self._repo = repo

    def score(
        self,
        *,
        application: Application,
        candidate: CandidateProfile,
        job: Job,
        evaluations: list[CriterionEvaluation],
        blind_mode: bool = False,
    ) -> ScoringResult:
        source_text = candidate.raw_text or "\n".join(candidate.raw_chunks)
        if blind_mode:
            source_text = self._redactor.redact(
                source_text, blind_mode=True, full_name=candidate.full_name
            ).text

        criteria = _criteria_index(tuple(job.rubric))
        composite = 0.0
        criterion_scores: list[CriterionScore] = []
        gaps: list[GapProbe] = []
        trusted_quotes: list[str] = []

        for evaluation in evaluations:
            criterion = criteria.get(evaluation.criterion_id)
            if criterion is None:
                gaps.append(
                    GapProbe("missing_mandatory_criterion", evaluation.criterion_id, "criterion is not in the job rubric")
                )
                continue

            citations = self._verifier.verify_many(evaluation.citations, source_text)
            verified = [citation for citation in citations if citation.verified]
            confidence = evaluation.confidence
            rationale = evaluation.rationale

            if not verified:
                rationale = ""
                confidence = max(0.0, confidence * FULL_REJECTION_FACTOR)
                gaps.append(
                    GapProbe("unsubstantiated_skill", criterion.id, "no citation passed deterministic source verification")
                )
            elif len(verified) < len(citations):
                confidence = max(0.0, confidence * PARTIAL_REJECTION_FACTOR)

            if criterion.mandatory and not verified:
                gaps.append(
                    GapProbe("missing_mandatory_criterion", criterion.id, "mandatory criterion lacks verified evidence")
                )

            bounded_score = max(0, min(MAX_SCORE, evaluation.score))
            composite += bounded_score * criterion.weight / 100.0
            trusted_quotes.extend(citation.quote for citation in verified)
            criterion_scores.append(
                CriterionScore(
                    criterion_id=criterion.id,
                    criterion_name=criterion.name,
                    weight=criterion.weight,
                    score=bounded_score,
                    rationale=rationale,
                    citations=verified,
                    confidence=confidence,
                )
            )

        evidence = normalize(" ".join(trusted_quotes))
        for skill in candidate.skills:
            if skill and normalize(skill) not in evidence:
                gaps.append(
                    GapProbe("unsubstantiated_skill", "profile", f"skill '{skill}' has no verified evidence")
                )

        result = ScoringResult(
            application_id=application.id,
            candidate_id=application.candidate_id,
            composite_score=composite,
            criterion_scores=criterion_scores,
            gaps_and_probes=gaps,
            blind_mode=blind_mode,
        )
        self._repo.save_scoring_result(result)
        return result
