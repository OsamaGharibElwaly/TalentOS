from dataclasses import replace

import pytest

from app.adapters.offline_extractor import OfflineExtractor, build_inference_backend, validate_profile
from app.domain.exceptions import InferenceConfigError, ProfileValidationError
from app.domain.models import CandidateProfile, EducationEntry, ExperienceEntry


def make_profile(**overrides: object) -> CandidateProfile:
    base = CandidateProfile(
        full_name="  Jane Doe  ",
        email="Jane.Doe@Example.com",
        phone="+1 555 123 4567",
        links=[" https://linkedin.com/in/jane "],
        total_experience_years=5.0,
        skills=["Python", "python", " SQL "],
        experience_entries=[ExperienceEntry("Engineer", "Acme", 60, ["Built APIs"])],
        education=[EducationEntry("State U", "BSc", "2016")],
        raw_chunks=["Jane Doe", "EXPERIENCE"],
    )
    return replace(base, **overrides)  # type: ignore[arg-type]


def test_valid_profile_is_canonicalized() -> None:
    profile = validate_profile(make_profile())
    assert profile.full_name == "Jane Doe"
    assert profile.email == "jane.doe@example.com"
    assert profile.skills == ["python", "sql"]
    assert profile.links == ["https://linkedin.com/in/jane"]


def test_extractor_normalizes_and_derives_years_from_durations() -> None:
    text = "Jane Doe\njane@example.com\nEXPERIENCE\nEngineer | Acme | 36 months\n- Built APIs"
    profile = OfflineExtractor().extract_profile(text, [text])
    assert profile.full_name == "Jane Doe"
    assert profile.email == "jane@example.com"
    assert profile.total_experience_years == 3.0
    assert profile.experience_entries[0].duration_months == 36
    assert profile.skills == sorted(set(profile.skills))
    assert "python" not in profile.skills


def test_malformed_email_is_rejected() -> None:
    with pytest.raises(ProfileValidationError):
        validate_profile(make_profile(email="not-an-email"))


def test_profile_without_any_contact_is_rejected() -> None:
    with pytest.raises(ProfileValidationError):
        validate_profile(make_profile(email="", phone=""))


def test_bounded_schema_rejects_oversized_fields() -> None:
    with pytest.raises(ProfileValidationError):
        validate_profile(make_profile(skills=[f"skill-{index}" for index in range(101)]))
    with pytest.raises(ProfileValidationError):
        validate_profile(make_profile(raw_chunks=["x" for _ in range(201)]))


def test_repair_loop_is_bounded_to_two_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def always_invalid(profile: CandidateProfile) -> CandidateProfile:
        calls.append(1)
        raise ProfileValidationError("forced")

    monkeypatch.setattr("app.adapters.offline_extractor.validate_profile", always_invalid)
    with pytest.raises(ProfileValidationError):
        OfflineExtractor().extract_profile("Jane Doe jane@example.com", [], retries=2)
    assert len(calls) == 3


def test_inference_backend_defaults_offline_and_fails_closed() -> None:
    assert isinstance(build_inference_backend("offline"), OfflineExtractor)
    with pytest.raises(InferenceConfigError):
        build_inference_backend("paid-llm")
