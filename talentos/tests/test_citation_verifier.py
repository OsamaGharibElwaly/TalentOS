import pytest

from app.services.citation_verifier import (
    CitationVerifier,
    normalize,
    token_sequence_overlap,
)

RAW = "Jane Doe built Python services at Acme Corp with strong SQL skills."


@pytest.fixture()
def verifier() -> CitationVerifier:
    return CitationVerifier()


def test_exact_citation_is_verified(verifier: CitationVerifier) -> None:
    result = verifier.verify("built Python services", RAW)
    assert result.verified is True
    assert result.similarity == 1.0
    assert result.quote == "built Python services"


def test_whitespace_and_case_are_normalized(verifier: CitationVerifier) -> None:
    assert verifier.verify("  BUILT   python\nservices  ", RAW).verified is True
    assert normalize("  A\tB\nC ") == "a b c"


def test_fabricated_quote_is_caught_and_rejected(verifier: CitationVerifier) -> None:
    result = verifier.verify("led a team of 50 engineers", RAW)
    assert result.verified is False
    assert result.similarity < 0.90


def test_empty_quote_is_rejected(verifier: CitationVerifier) -> None:
    result = verifier.verify("   ", RAW)
    assert result.verified is False
    assert result.similarity == 0.0


def test_token_sequence_overlap_threshold() -> None:
    assert token_sequence_overlap("a b c d e f g h i j".split(), "a b c d e f g h i j".split()) == 1.0
    assert token_sequence_overlap("a b c".split(), "a b x".split()) == pytest.approx(2 / 3)
    verifier = CitationVerifier()
    assert verifier.verify("a b c d e f g h i X", "a b c d e f g h i j").verified is True
    assert verifier.verify("a b c d e f g h X Y", "a b c d e f g h i j").verified is False


def test_verify_many_keeps_results_aligned() -> None:
    results = CitationVerifier().verify_many(["built Python services", "managed 50 staff"], RAW)
    assert [result.verified for result in results] == [True, False]
