import pytest

from app.domain.exceptions import RubricValidationError
from app.domain.models import RubricCriterion
from app.services.job_service import validate_rubric


def criterion(index: int, weight: float, name: str | None = None) -> RubricCriterion:
    return RubricCriterion(id=f"c{index}", name=name or f"Criterion {index}", weight=weight)


def test_valid_rubric_sums_to_one() -> None:
    validate_rubric([criterion(1, 0.5), criterion(2, 0.3), criterion(3, 0.2)])


def test_valid_rubric_within_tolerance() -> None:
    validate_rubric([criterion(1, 0.5000001), criterion(2, 0.4999999)])


def test_empty_rubric_rejected() -> None:
    with pytest.raises(RubricValidationError):
        validate_rubric([])


def test_weights_must_sum_to_one() -> None:
    with pytest.raises(RubricValidationError):
        validate_rubric([criterion(1, 0.5), criterion(2, 0.2)])


@pytest.mark.parametrize("weight", [0.0, -0.1])
def test_non_positive_weight_rejected(weight: float) -> None:
    with pytest.raises(RubricValidationError):
        validate_rubric([criterion(1, weight), criterion(2, 1.0 - weight)])


def test_duplicate_ids_rejected() -> None:
    with pytest.raises(RubricValidationError):
        validate_rubric(
            [criterion(1, 0.5), RubricCriterion(id="c1", name="Other", weight=0.5)]
        )


def test_blank_name_rejected() -> None:
    with pytest.raises(RubricValidationError):
        validate_rubric([criterion(1, 1.0, name="   ")])
