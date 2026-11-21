from __future__ import annotations

import re

from app.domain.enums import HireRecommendation
from app.domain.models import (
    CandidateProfile,
    CriterionRating,
    InterviewQuestion,
    InterviewScorecard,
    Job,
    ResumeDiscrepancy,
    RubricCriterion,
    ScoringResult,
)
from app.services.citation_verifier import normalize

_TOKEN_RE = re.compile(r"[a-z0-9+#.]+")
_NEGATION_RE = re.compile(
    r"\b(?:no|not|never|without|hasn't|haven't|didn't|couldn't|cannot|can't|unfamiliar|weak|shaky)\b"
)
_POSITIVE_MARKERS = ("strong", "excellent", "impressed", "clear", "solid", "good", "confident", "deep")
_NEGATIVE_MARKERS = ("weak", "unclear", "struggled", "couldn't", "didn't", "shaky", "superficial", "vague")


def _terms(value: str) -> set[str]:
    return {token for token in _TOKEN_RE.findall(normalize(value)) if len(token) >= 3}


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"[.!?\n]+", text) if part.strip()]


def _unique(items: list[str], limit: int = 5) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
        if len(result) >= limit:
            break
    return result


class InterviewCopilot:
    """Deterministic, rubric-grounded question generation and note synthesis."""

    def generate_questions(
        self,
        candidate: CandidateProfile,
        job: Job,
        scoring_result: ScoringResult | None = None,
    ) -> list[InterviewQuestion]:
        gap_details: dict[str, str] = {}
        if scoring_result is not None:
            for gap in scoring_result.gaps_and_probes:
                if gap.criterion_id != "profile" and gap.criterion_id not in gap_details:
                    gap_details[gap.criterion_id] = gap.detail

        criteria: list[RubricCriterion] = job.rubric or [
            RubricCriterion("general", "the role", 1.0)
        ]
        ordered = sorted(criteria, key=lambda criterion: criterion.id not in gap_details)
        count = min(max(5, len(criteria)), 8)
        source = candidate.raw_text or "\n".join(candidate.raw_chunks)
        lines = [line.strip() for line in source.splitlines() if line.strip()]

        questions: list[InterviewQuestion] = []
        for index in range(count):
            criterion = ordered[index % len(ordered)]
            detail = gap_details.get(criterion.id)
            if detail:
                text = (
                    f"Tell me about your experience with {criterion.name}. "
                    f"Our resume review flagged a gap: {detail}."
                )
            elif index >= len(ordered):
                text = f"Give another specific example that demonstrates {criterion.name}."
            else:
                text = (
                    f"Describe a specific project where you demonstrated {criterion.name}. "
                    "What did you do and what was the outcome?"
                )

            terms = _terms(criterion.name)
            for skill in candidate.skills:
                terms |= _terms(skill)
            context = next(
                (line[:240] for line in lines if terms & _terms(line)),
                lines[0][:240] if lines else "No resume context available.",
            )
            strong = [
                f"Describes a concrete project using {criterion.name} with measurable impact",
                "Quantifies their own contribution and the result",
            ]
            red_flags = [
                f"Cannot explain how {criterion.name} was applied in practice",
                "Answers stay hypothetical with no specific example",
            ]
            if detail:
                red_flags.append(f"Gap under review: {detail}")
            questions.append(
                InterviewQuestion(text, criterion.id, context, strong, red_flags)
            )
        return questions

    def synthesize_notes(
        self,
        raw_notes: str,
        candidate: CandidateProfile,
        job: Job,
        *,
        candidate_id: str = "",
    ) -> InterviewScorecard:
        sentences = _sentences(raw_notes)
        ratings: list[CriterionRating] = []
        strengths: list[str] = []
        concerns: list[str] = []

        for criterion in job.rubric:
            matched = [sentence for sentence in sentences if _terms(criterion.name) & _terms(sentence)]
            positive_sentences: list[str] = []
            negative_sentences: list[str] = []
            for sentence in matched:
                normalized = normalize(sentence)
                has_positive = any(marker in normalized for marker in _POSITIVE_MARKERS)
                has_negative = any(marker in normalized for marker in _NEGATIVE_MARKERS)
                if has_positive and not has_negative:
                    positive_sentences.append(sentence)
                elif has_negative and not has_positive:
                    negative_sentences.append(sentence)
            strengths.extend(positive_sentences)
            concerns.extend(negative_sentences)
            if not matched:
                rating = 0
            elif len(positive_sentences) > len(negative_sentences):
                rating = 5
            elif len(negative_sentences) > len(positive_sentences):
                rating = 2
            else:
                rating = 3
            ratings.append(
                CriterionRating(criterion.id, criterion.name, rating, matched[0][:240] if matched else "")
            )

        discrepancies: list[ResumeDiscrepancy] = []
        for skill in candidate.skills:
            needle = normalize(skill)
            if not needle:
                continue
            for sentence in sentences:
                normalized = normalize(sentence)
                position = normalized.find(needle)
                if position < 0:
                    continue
                window = normalized[max(0, position - 40) : position + len(needle) + 40]
                if _NEGATION_RE.search(window):
                    discrepancies.append(ResumeDiscrepancy(skill, sentence[:240]))
                    break

        years_match = re.search(r"\b(?:only|just)\s+(\d{1,2})\s+years?\b", normalize(raw_notes))
        if years_match and int(years_match.group(1)) < candidate.total_experience_years:
            discrepancies.append(
                ResumeDiscrepancy(
                    f"{candidate.total_experience_years:g} years experience",
                    f"Interviewer noted only {years_match.group(1)} years.",
                )
            )

        assessed = [rating.rating for rating in ratings if rating.rating]
        average = sum(assessed) / len(assessed) if assessed else 0.0
        if not raw_notes.strip() or discrepancies:
            recommendation = HireRecommendation.NEEDS_REVIEW
        elif average >= 4.5:
            recommendation = HireRecommendation.STRONG_HIRE
        elif average >= 3.5:
            recommendation = HireRecommendation.HIRE
        else:
            recommendation = HireRecommendation.NO_HIRE

        return InterviewScorecard(
            candidate_id=candidate_id,
            job_id=job.id,
            criterion_ratings=ratings,
            strengths=_unique(strengths),
            concerns=_unique(concerns),
            resume_discrepancies=discrepancies,
            hire_recommendation=recommendation,
            raw_notes=raw_notes,
        )
