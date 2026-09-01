"""Behavior tests for HRP-44 domain classification."""

from hr_pro_platform.transformation.classifier import UNKNOWN, classify_payload


def test_exact_personal_shape_is_classified_as_personal_ac01() -> None:
    payload = {
        "name": "x",
        "last_name": "x",
        "sex": [],
        "telfnumber": "x",
        "passport": "x",
        "email": "x",
    }
    assert classify_payload(payload) == "Personal"


def test_exact_location_shape_is_classified_as_location_ac02() -> None:
    assert classify_payload({"fullname": "x", "city": "x", "address": "x"}) == "Location"


def test_exact_professional_shape_is_classified_as_professional_ac03() -> None:
    payload = {
        "fullname": "x",
        "company": "x",
        "company address": "x",
        "company_telfnumber": "x",
        "company_email": "x",
        "job": "x",
    }
    assert classify_payload(payload) == "Professional"


def test_exact_bank_shape_is_classified_as_bank_ac04() -> None:
    assert classify_payload({"passport": "x", "IBAN": "x", "salary": "anything"}) == "Bank"


def test_exact_net_shape_is_classified_as_net_ac05() -> None:
    assert classify_payload({"address": "not-an-ip", "IPv4": "not-an-address"}) == "Net"


def test_classification_ignores_order_and_values_and_is_repeatable_ac06() -> None:
    first = {
        "name": "first",
        "last_name": "first",
        "sex": [],
        "telfnumber": "first",
        "passport": "first",
        "email": "first",
    }
    second = {
        "email": "second",
        "passport": "second",
        "telfnumber": "second",
        "sex": ["other"],
        "last_name": "second",
        "name": "second",
    }
    assert classify_payload(first) == classify_payload(second) == "Personal"
    assert classify_payload(second) == "Personal"


def test_missing_extra_partial_and_unsupported_shapes_are_unknown_ac07() -> None:
    assert classify_payload({"fullname": "x", "city": "x"}) == UNKNOWN
    assert classify_payload({"fullname": "x", "city": "x", "address": "x", "extra": "x"}) == UNKNOWN
    assert classify_payload({"passport": "x", "IBAN": "x"}) == UNKNOWN
    assert classify_payload({"unrecognized": "x"}) == UNKNOWN


def test_classification_does_not_mutate_payload_ac08() -> None:
    payload = {"address": "x", "IPv4": "y"}
    original = payload.copy()
    assert classify_payload(payload) == "Net"
    assert payload == original
