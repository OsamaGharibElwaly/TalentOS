from __future__ import annotations

import re

from app.domain.enums import ApplicationStage
from app.domain.models import TalentSearchResult
from app.ports.repositories import RepositoryPort
from app.ports.vector_index import VectorIndexPort
from app.services.citation_verifier import normalize

_WORD_RE = re.compile(r"[a-z0-9+#.]+")


def _excerpt(query: str, text: str) -> str:
    source = text.strip()
    if not source:
        return ""
    terms = sorted(
        {term for term in _WORD_RE.findall(query.lower()) if len(term) >= 2},
        key=len,
        reverse=True,
    )
    lowered = source.lower()
    positions = [lowered.find(term) for term in terms]
    matches = [position for position in positions if position >= 0]
    if not matches:
        words = source.split()
        return " ".join(words[:60]) + ("..." if len(words) > 60 else "")
    start = max(0, min(matches) - 120)
    end = min(len(source), max(matches) + 200)
    excerpt = source[start:end]
    if terms:
        pattern = re.compile("|".join(re.escape(term) for term in terms), re.I)
        excerpt = pattern.sub(lambda match: f"<mark>{match.group(0)}</mark>", excerpt)
    return ("..." if start else "") + excerpt + ("..." if end < len(source) else "")


class TalentSearchService:
    """SQL-filtered candidates ranked by local hybrid-index similarity."""

    def __init__(self, repo: RepositoryPort, index: VectorIndexPort) -> None:
        self._repo = repo
        self._index = index

    def search(
        self,
        tenant_id: str,
        query: str,
        *,
        min_experience_years: float | None = None,
        required_skills: list[str] | None = None,
        stage: ApplicationStage | str | None = None,
        top_k: int = 10,
    ) -> list[TalentSearchResult]:
        if top_k < 1:
            return []
        hits = self._index.search(tenant_id, query, top_k=max(top_k * 20, 100))
        candidates = {candidate.id: candidate for candidate in self._repo.list_candidates(tenant_id)}
        applications = self._repo.list_applications(tenant_id)
        wanted_stage = ApplicationStage(stage) if stage is not None else None
        required = {normalize(skill) for skill in (required_skills or []) if normalize(skill)}

        results: list[TalentSearchResult] = []
        for hit in hits:
            candidate = candidates.get(hit.doc_id)
            if candidate is None:
                continue
            profile = candidate.profile
            if min_experience_years is not None and profile.total_experience_years < min_experience_years:
                continue
            if required and not required <= {normalize(skill) for skill in profile.skills}:
                continue
            if wanted_stage is not None and not any(
                application.candidate_id == candidate.id and application.stage == wanted_stage
                for application in applications
            ):
                continue
            results.append(
                TalentSearchResult(
                    candidate_id=candidate.id,
                    profile=profile,
                    score=hit.score,
                    highlighted_excerpt=_excerpt(query, profile.raw_text or " ".join(profile.raw_chunks)),
                )
            )
            if len(results) >= top_k:
                break
        return results
