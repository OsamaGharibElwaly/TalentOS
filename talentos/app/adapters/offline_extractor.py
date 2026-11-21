from __future__ import annotations

import re
from dataclasses import replace

from app.domain.exceptions import InferenceConfigError, ProfileValidationError
from app.domain.models import CandidateProfile, EducationEntry, ExperienceEntry
from app.ports.inference import InferencePort

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
LINK_RE = re.compile(r"https?://[^\s<>()]+")
YEARS_RE = re.compile(r"(\d{1,2})\s*\+?\s*years?", re.I)
MONTHS_RE = re.compile(r"(\d{1,3})\s*months?", re.I)
YEAR_RANGE_RE = re.compile(r"(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}")
HEADING_RE = re.compile(
    r"^(?:#{1,6}\s*)?(SUMMARY|EXPERIENCE|EDUCATION|SKILLS|LINKS|CONTACT)\s*:?\s*$", re.I
)

COMMON_SKILLS = (
    "python", "sql", "fastapi", "django", "flask", "javascript", "typescript",
    "react", "node", "java", "go", "rust", "c++", "docker", "kubernetes",
    "aws", "azure", "gcp", "git", "postgresql", "mysql", "redis", "mongodb",
    "pandas", "numpy", "pytest", "linux", "rest", "graphql", "agile",
)


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"HEADER": []}
    current = "HEADER"
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if not line:
            continue
        match = HEADING_RE.match(line)
        if match:
            current = match.group(1).upper()
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return sections


def validate_profile(profile: CandidateProfile) -> CandidateProfile:
    """Bounded schema check; raises on violations that repair cannot fix."""
    canonical = replace(
        profile,
        full_name=_clean(profile.full_name),
        email=_clean(profile.email).lower(),
        phone=_clean(profile.phone),
        links=[_clean(link) for link in profile.links],
        skills=list(dict.fromkeys(_clean(skill).lower() for skill in profile.skills if _clean(skill))),
        raw_chunks=[chunk.strip() for chunk in profile.raw_chunks if chunk.strip()],
    )
    if not canonical.full_name or len(canonical.full_name) > 120:
        raise ProfileValidationError("full_name must be 1-120 characters")
    if canonical.email and not EMAIL_RE.fullmatch(canonical.email):
        raise ProfileValidationError("email is malformed")
    if not canonical.email and not canonical.phone:
        raise ProfileValidationError("a profile needs an email or phone")
    if canonical.phone and not 7 <= sum(c.isdigit() for c in canonical.phone) <= 15:
        raise ProfileValidationError("phone must contain 7-15 digits")
    if any(not link.startswith(("http://", "https://")) for link in canonical.links):
        raise ProfileValidationError("links must be http(s) URLs")
    if len(canonical.links) > 20 or len(canonical.skills) > 100:
        raise ProfileValidationError("links or skills exceed schema bounds")
    if any(len(skill) > 40 for skill in canonical.skills):
        raise ProfileValidationError("skill tag exceeds 40 characters")
    if not 0.0 <= canonical.total_experience_years <= 60.0:
        raise ProfileValidationError("total_experience_years out of range")
    if len(canonical.experience_entries) > 50 or len(canonical.education) > 20:
        raise ProfileValidationError("experience or education exceeds schema bounds")
    for entry in canonical.experience_entries:
        if not 0 <= entry.duration_months <= 600:
            raise ProfileValidationError("duration_months out of range")
    if len(canonical.raw_chunks) > 200 or any(len(chunk) > 5000 for chunk in canonical.raw_chunks):
        raise ProfileValidationError("raw_chunks exceed schema bounds")
    return canonical


class OfflineExtractor(InferencePort):
    """Deterministic, zero-cost profile extraction from normalized text."""

    def extract_profile(
        self, text: str, chunks: list[str], *, retries: int = 2
    ) -> CandidateProfile:
        profile = self._extract(text, chunks)
        for attempt in range(retries + 1):
            try:
                return validate_profile(profile)
            except ProfileValidationError:
                if attempt >= retries:
                    raise
                profile = self._repair(profile, text, attempt)
        raise ProfileValidationError("profile extraction failed")

    def _extract(self, text: str, chunks: list[str]) -> CandidateProfile:
        sections = _sections(text)
        header = sections.get("HEADER", [])
        lines = header + [line for group in sections.values() for line in group]

        full_name = ""
        for line in header[:8]:
            words = line.split()
            if 2 <= len(words) <= 4 and all(word.replace(".", "").isalpha() for word in words):
                full_name = line
                break

        email_match = EMAIL_RE.search(text)
        phone_match = PHONE_RE.search(text)
        links = LINK_RE.findall(text)

        skill_lines = sections.get("SKILLS", [])
        skills = [
            token.strip(" -*")
            for line in skill_lines
            for token in re.split(r"[,;|]", line)
            if token.strip(" -*")
        ]
        lowered = " " + text.lower() + " "
        skills.extend(skill for skill in COMMON_SKILLS if re.search(rf"\b{re.escape(skill)}\b", lowered))

        experience: list[ExperienceEntry] = []
        highlights: list[str] = []
        for line in sections.get("EXPERIENCE", []):
            if line.startswith("-") or line.startswith("*"):
                highlights.append(line.lstrip("-* "))
                continue
            parts = [part.strip() for part in line.split("|")]
            title, company, duration_text = parts[0], "", ""
            if len(parts) >= 2:
                company = parts[1]
                duration_text = " | ".join(parts[2:])
            else:
                match = re.search(r"(.+?)\s+at\s+(.+?)\s+(\d+\s*months?)", line, re.I)
                if match:
                    title, company, duration_text = match.groups()
            duration = self._duration_months(duration_text)
            experience.append(ExperienceEntry(title, company, duration, highlights))
            highlights = []

        education: list[EducationEntry] = []
        for line in sections.get("EDUCATION", []):
            parts = [part.strip() for part in line.split("|")]
            education.append(
                EducationEntry(
                    school=parts[0],
                    degree=parts[1] if len(parts) > 1 else "",
                    year=parts[2] if len(parts) > 2 else "",
                )
            )

        years_match = YEARS_RE.search(text)
        if years_match:
            total_years = float(years_match.group(1))
        else:
            total_years = round(sum(entry.duration_months for entry in experience) / 12, 2)

        return CandidateProfile(
            full_name=full_name,
            email=email_match.group(0) if email_match else "",
            phone=phone_match.group(0) if phone_match else "",
            links=links,
            total_experience_years=total_years,
            skills=skills,
            experience_entries=experience,
            education=education,
            raw_chunks=chunks,
            raw_text=text,
        )

    @staticmethod
    def _duration_months(value: str) -> int:
        match = MONTHS_RE.search(value)
        if match:
            return int(match.group(1))
        span = YEAR_RANGE_RE.search(value)
        if span:
            return (int(span.group(2)) - int(span.group(1))) * 12
        return 0

    @staticmethod
    def _repair(
        profile: CandidateProfile, text: str, attempt: int
    ) -> CandidateProfile:
        repairs: dict[str, object] = {}
        if not _clean(profile.full_name):
            repairs["full_name"] = (
                "Unknown Candidate" if attempt >= 1 else OfflineExtractor._first_words(text)
            )
        if not profile.total_experience_years and profile.experience_entries:
            repairs["total_experience_years"] = round(
                sum(entry.duration_months for entry in profile.experience_entries) / 12, 2
            )
        repairs["links"] = [link for link in profile.links if link.startswith(("http://", "https://"))][:20]
        if attempt >= 1:
            if not profile.email and not profile.phone:
                digits = re.sub(r"\D", "", text)
                if 7 <= len(digits) <= 15:
                    repairs["phone"] = digits
            repairs["total_experience_years"] = min(max(profile.total_experience_years, 0.0), 60.0)
            repairs["skills"] = [skill[:40] for skill in profile.skills][:100]
            repairs["raw_chunks"] = [chunk[:5000] for chunk in profile.raw_chunks][:200]
        return replace(profile, **repairs)

    @staticmethod
    def _first_words(text: str) -> str:
        for line in text.replace("\r\n", "\n").split("\n"):
            words = line.strip().split()
            if 2 <= len(words) <= 4 and all(word.isalpha() for word in words):
                return _clean(line)
        return ""


def build_inference_backend(name: str) -> InferencePort:
    """Only the offline backend is bundled; others fail fast without network calls."""
    if name != "offline":
        raise InferenceConfigError(
            f"inference backend {name!r} is not installed; use 'offline'"
        )
    return OfflineExtractor()
