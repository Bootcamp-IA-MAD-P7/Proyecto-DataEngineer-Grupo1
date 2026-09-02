"""Behavior tests for HRP-48 Bank operational grouping."""

from copy import deepcopy

from hr_pro_platform.transformation.bank_grouper import (
    ClassifiedFragment,
    JSONValue,
    group_bank_fragments,
)
from hr_pro_platform.transformation.classifier import UNKNOWN


def bank(passport: JSONValue, iban: JSONValue = "synthetic") -> dict[str, JSONValue]:
    return {"passport": passport, "IBAN": iban, "salary": "synthetic-salary"}


def fragment(payload: JSONValue, classification: str = "Bank") -> ClassifiedFragment:
    return ClassifiedFragment(payload=payload, classification=classification)


def test_valid_bank_payload_is_retained_ac01() -> None:
    payload = bank("P-001")
    result = group_bank_fragments([fragment(payload)])
    assert result.groups[0].key == "P-001"
    assert result.groups[0].fragments == (payload,)


def test_same_and_different_passports_define_domain_local_groups_ac02() -> None:
    result = group_bank_fragments([fragment(bank("P-001")), fragment(bank("P-002"))])
    assert [group.key for group in result.groups] == ["P-001", "P-002"]
    assert not hasattr(result.groups[0], "person_id")


def test_duplicate_bank_payloads_are_deterministic_ac03() -> None:
    first = [fragment(bank("P-001")), fragment(bank("P-002"))]
    second = list(reversed(first + [fragment(bank("P-001"))]))
    assert group_bank_fragments(first) == group_bank_fragments(second)
    assert len(group_bank_fragments(second).groups[0].fragments) == 1


def test_missing_bank_passport_is_unsupported_ac04() -> None:
    result = group_bank_fragments([fragment({"IBAN": "synthetic", "salary": "synthetic-salary"})])
    assert result.unresolved[0].status == "unsupported"
    assert result.unresolved[0].reason == "classification_mismatch"


def test_unusable_bank_passport_is_uncorrelated_ac04() -> None:
    result = group_bank_fragments([fragment(bank("")), fragment(bank(None)), fragment(bank(42))])
    assert len(result.unresolved) == 3
    assert all(item.status == "uncorrelated" for item in result.unresolved)


def test_distinct_same_passport_evidence_is_ambiguous_ac05() -> None:
    first = bank("P-001", "one")
    second = bank("P-001", "two")
    result = group_bank_fragments([fragment(first), fragment(second)])
    assert result.groups[0].status == "ambiguous"
    assert len(result.groups[0].fragments) == 2
    assert first in result.groups[0].fragments
    assert second in result.groups[0].fragments


def test_unsupported_bank_input_is_explicit_ac06() -> None:
    result = group_bank_fragments(
        [fragment({}, UNKNOWN), fragment(bank("P-001"), "Personal"), fragment([])]
    )
    assert len(result.unresolved) == 3
    assert all(item.status == "unsupported" for item in result.unresolved)


def test_bank_grouping_preserves_payload_and_context_ac07() -> None:
    payload = bank("  P-001  ")
    original = deepcopy(payload)
    context = fragment(payload)
    result = group_bank_fragments([context])
    assert payload == original
    assert context == fragment(payload)
    assert result.groups[0].key == "  P-001  "


def test_bank_grouping_has_no_normalization_fallback_or_identity_ac08() -> None:
    result = group_bank_fragments([fragment(bank("p-001")), fragment(bank("P-001"))])
    assert [group.key for group in result.groups] == ["P-001", "p-001"]
    assert not hasattr(result, "person_id")
