from __future__ import annotations

import re

from app.domain.models import Citation

SIMILARITY_THRESHOLD = 0.90
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _tokens(value: str) -> list[str]:
    return _TOKEN_RE.findall(normalize(value))


def token_sequence_overlap(quote_tokens: list[str], source_tokens: list[str]) -> float:
    if not quote_tokens or not source_tokens:
        return 0.0
    window = min(len(quote_tokens), len(source_tokens))
    best = 0.0
    for start in range(len(source_tokens) - window + 1):
        candidate = source_tokens[start : start + window]
        matches = sum(
            1 for left, right in zip(quote_tokens[:window], candidate) if left == right
        )
        best = max(best, matches / len(quote_tokens))
    return best


class CitationVerifier:
    """Deterministically checks quoted evidence against the candidate's raw text."""

    def verify(self, quote: str, raw_text: str) -> Citation:
        normalized_quote = normalize(quote)
        if not normalized_quote:
            return Citation(quote, False, 0.0)
        if normalized_quote in normalize(raw_text):
            return Citation(quote, True, 1.0)
        similarity = token_sequence_overlap(_tokens(quote), _tokens(raw_text))
        return Citation(quote, similarity >= SIMILARITY_THRESHOLD, round(similarity, 6))

    def verify_many(self, quotes: list[str], raw_text: str) -> list[Citation]:
        return [self.verify(quote, raw_text) for quote in quotes]
