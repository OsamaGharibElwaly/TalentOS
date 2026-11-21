from typing import Protocol

from app.domain.models import CandidateProfile


class InferencePort(Protocol):
    def extract_profile(
        self, text: str, chunks: list[str], *, retries: int = 2
    ) -> CandidateProfile: ...
