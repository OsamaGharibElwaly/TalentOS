from app.domain.enums import HireRecommendation
from app.domain.models import (
    CandidateProfile,
    EducationEntry,
    ExperienceEntry,
    GapProbe,
    Job,
    RubricCriterion,
    ScoringResult,
)
from app.services.interview_copilot import InterviewCopilot

RAW = """Alice Smith
EXPERIENCE
Built Python services at Acme with SQL reporting
Collaborated with designers on delivery
SKILLS
Python, SQL
"""


def candidate() -> CandidateProfile:
    return CandidateProfile(
        full_name="Alice Smith",
        email="alice@example.com",
        phone="+1 555 123 4567",
        links=[],
        total_experience_years=8.0,
        skills=["python", "sql"],
        experience_entries=[ExperienceEntry("Engineer", "Acme", 96, [])],
        education=[EducationEntry("State U", "BSc", "2016")],
        raw_chunks=["Alice Smith", "EXPERIENCE"],
        raw_text=RAW,
    )


def job() -> Job:
    return Job(
        id="job-1",
        tenant_id="org-1",
        title="Senior Engineer",
        rubric=[
            RubricCriterion("eng", "Engineering", 0.6, mandatory=True),
            RubricCriterion("collab", "Collaboration", 0.4),
        ],
        created_by="admin",
    )


def scoring_result() -> ScoringResult:
    return ScoringResult(
        application_id="app-1",
        candidate_id="cand-1",
        composite_score=0.5,
        criterion_scores=[],
        gaps_and_probes=[
            GapProbe("missing_mandatory_criterion", "eng", "mandatory criterion lacks verified evidence")
        ],
        blind_mode=False,
    )


def test_generates_five_to_eight_criterion_mapped_questions() -> None:
    questions = InterviewCopilot().generate_questions(candidate(), job(), scoring_result())
    assert 5 <= len(questions) <= 8
    assert {question.target_criterion for question in questions} == {"eng", "collab"}
    for question in questions:
        assert question.text
        assert question.resume_context
        assert question.strong_signal_indicators
        assert question.red_flag_indicators


def test_questions_are_grounded_in_scoring_gaps() -> None:
    questions = InterviewCopilot().generate_questions(candidate(), job(), scoring_result())
    assert questions[0].target_criterion == "eng"
    assert "mandatory criterion lacks verified evidence" in questions[0].text
    assert any("mandatory criterion lacks verified evidence" in flag for flag in questions[0].red_flag_indicators)


def test_resume_context_quotes_the_relevant_resume_line() -> None:
    questions = InterviewCopilot().generate_questions(candidate(), job())
    engineering = next(question for question in questions if question.target_criterion == "eng")
    assert "Python" in engineering.resume_context


def test_scorecard_flags_contradiction_and_preserves_raw_notes() -> None:
    notes = (
        "Engineering: strong Python delivery.\n"
        "Collaboration: unclear communication.\n"
        "No Python experience in practice."
    )
    scorecard = InterviewCopilot().synthesize_notes(
        notes, candidate(), job(), candidate_id="cand-1"
    )
    assert scorecard.raw_notes == notes
    assert scorecard.candidate_id == "cand-1"
    claims = {discrepancy.claim for discrepancy in scorecard.resume_discrepancies}
    assert "python" in claims
    assert scorecard.hire_recommendation == HireRecommendation.NEEDS_REVIEW


def test_scorecard_splits_strengths_concerns_and_rates_criteria() -> None:
    notes = (
        "Engineering: strong and clear Python delivery.\n"
        "Collaboration: excellent teamwork with designers.\n"
        "Collaboration: vague examples of conflict resolution."
    )
    scorecard = InterviewCopilot().synthesize_notes(notes, candidate(), job())
    ratings = {rating.criterion_id: rating.rating for rating in scorecard.criterion_ratings}
    assert ratings == {"eng": 5, "collab": 3}
    assert scorecard.strengths
    assert scorecard.concerns
    assert all("vague" in concern or "Collaboration" in concern for concern in scorecard.concerns)


def test_clean_strong_notes_produce_hire_recommendation() -> None:
    notes = (
        "Engineering: strong and clear Python delivery.\n"
        "Collaboration: excellent communication with the team."
    )
    scorecard = InterviewCopilot().synthesize_notes(notes, candidate(), job())
    assert scorecard.resume_discrepancies == []
    assert scorecard.hire_recommendation == HireRecommendation.STRONG_HIRE


def test_empty_notes_are_not_scored_as_a_hire() -> None:
    scorecard = InterviewCopilot().synthesize_notes("", candidate(), job())
    assert scorecard.hire_recommendation == HireRecommendation.NEEDS_REVIEW
    assert all(rating.rating == 0 for rating in scorecard.criterion_ratings)
