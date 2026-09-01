"""Behavior tests for the HRP-45 validation and cleaning boundary."""

from copy import deepcopy
from dataclasses import FrozenInstanceError

from hr_pro_platform.transformation.validator import ValidationResult, validate_fragment


def test_supported_classified_fragment_is_accepted_without_business_rules_ac01() -> None:
    payload = {"email": "not-an-email", "salary": "not-a-number"}

    result = validate_fragment(payload, "Personal")

    assert result.is_valid is True
    assert result.errors == ()
    assert result.payload is payload


def test_validation_is_deterministic_ac02() -> None:
    payload = {"value": "same"}

    assert validate_fragment(payload, "Net") == validate_fragment(payload, "Net")


def test_validation_does_not_mutate_input_payload_ac03() -> None:
    payload = {"nested": {"value": "  unchanged  "}}
    original = deepcopy(payload)

    validate_fragment(payload, "Location")

    assert payload == original


def test_non_mapping_payload_has_explicit_invalid_result_ac04() -> None:
    result = validate_fragment(["not", "an", "object"], "Personal")

    assert result.is_valid is False
    assert result.errors == ("payload_not_mapping",)
    assert result.payload is None


def test_unknown_classification_is_explicitly_rejected_ac05() -> None:
    payload = {"unresolved": "value"}

    result = validate_fragment(payload, "unknown")

    assert result.is_valid is False
    assert result.classification == "unknown"
    assert result.errors == ("unsupported_classification",)


def test_validation_has_no_identity_or_aggregation_behavior_ac06() -> None:
    result = validate_fragment({"passport": "same"}, "Bank")

    assert not hasattr(result, "person_id")
    assert result.payload == {"passport": "same"}


def test_values_are_preserved_without_cleaning_or_normalization_ac07() -> None:
    payload = {"value": "  MiXeD value  "}

    result = validate_fragment(payload, "Professional")

    assert result.payload == payload
    assert result.payload["value"] == "  MiXeD value  "


def test_validation_result_exposes_status_context_and_reasons_ac08() -> None:
    result = validate_fragment(None, "Personal")

    assert isinstance(result, ValidationResult)
    assert result.is_valid is False
    assert result.classification == "Personal"
    assert result.errors == ("payload_not_mapping",)


def test_unresolved_business_values_are_not_guessed_invalid_ac09() -> None:
    payload = {"email": "unknown-format", "IPv4": "unknown-format"}

    result = validate_fragment(payload, "Net")

    assert result.is_valid is True


def test_result_is_immutable_and_pure_boundary_is_explicit_ac10() -> None:
    result = validate_fragment({"field": "value"}, "Bank")

    assert result.errors == ()
    try:
        result.is_valid = False  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("ValidationResult must be immutable")
