"""Behavior tests for HRP-47 Professional operational grouping."""

from copy import deepcopy

from hr_pro_platform.transformation.classifier import UNKNOWN
from hr_pro_platform.transformation.professional_grouper import (
    ClassifiedFragment,
    JSONValue,
    group_professional_fragments,
)


def professional(fullname: JSONValue, company: JSONValue = "synthetic") -> dict[str, JSONValue]:
    return {
        "fullname": fullname,
        "company": company,
        "company address": "synthetic",
        "company_telfnumber": "synthetic",
        "company_email": "synthetic@example.test",
        "job": "synthetic",
    }


def fragment(
    payload: JSONValue, classification: str = "Professional", source: str = "source-1"
) -> ClassifiedFragment:
    return ClassifiedFragment(
        payload=payload, classification=classification, source_reference=source
    )


def test_valid_professional_payload_is_retained_ac01() -> None:
    payload = professional("Ada Example")
    result = group_professional_fragments([fragment(payload)])
    assert result.groups[0].key == "Ada Example"
    assert result.groups[0].fragments[0].payload == payload
    assert result.groups[0].fragments[0].source_reference == "source-1"


def test_same_and_different_approved_keys_define_domain_local_groups_ac02() -> None:
    result = group_professional_fragments(
        [fragment(professional("Ada Example", "one")), fragment(professional("Bob Example"))]
    )
    assert [group.key for group in result.groups] == ["Ada Example", "Bob Example"]
    assert not hasattr(result.groups[0], "person_id")


def test_duplicate_professional_payloads_are_deterministic_ac03() -> None:
    first = [fragment(professional("Ada Example")), fragment(professional("Bob Example"))]
    second = list(reversed(first + [fragment(professional("Ada Example"))]))
    assert group_professional_fragments(first) == group_professional_fragments(second)
    assert len(group_professional_fragments(second).groups[0].fragments) == 1


def test_missing_professional_key_is_unsupported_ac04() -> None:
    result = group_professional_fragments([fragment({"company": "synthetic"})])
    assert result.unresolved[0].status == "unsupported"
    assert result.unresolved[0].reason == "classification_mismatch"


def test_unusable_professional_key_is_uncorrelated_ac04() -> None:
    result = group_professional_fragments(
        [fragment(professional("")), fragment(professional(None)), fragment(professional(42))]
    )
    assert len(result.unresolved) == 3
    assert all(item.status == "uncorrelated" for item in result.unresolved)


def test_distinct_same_key_professional_evidence_is_ambiguous_ac05() -> None:
    first = professional("Ada Example", "one")
    second = professional("Ada Example", "two")
    result = group_professional_fragments([fragment(first), fragment(second)])
    assert result.groups[0].status == "ambiguous"
    assert len(result.groups[0].fragments) == 2
    assert [item.payload for item in result.groups[0].fragments] == [first, second]


def test_unsupported_professional_input_is_explicit_ac06() -> None:
    result = group_professional_fragments(
        [fragment({}, UNKNOWN), fragment(professional("Ada Example"), "Location"), fragment([])]
    )
    assert len(result.unresolved) == 3
    assert all(item.status == "unsupported" for item in result.unresolved)


def test_valid_non_professional_fragment_is_explicitly_unsupported_ac02() -> None:
    fragment = ClassifiedFragment(
        payload={"fullname": "Ada Example", "city": "synthetic", "address": "synthetic"},
        classification="Location",
        source_reference="location-source",
    )

    result = group_professional_fragments([fragment])

    assert result.groups == ()
    assert result.unresolved[0].status == "unsupported"
    assert result.unresolved[0].reason == "not_professional_fragment"


def test_professional_grouping_preserves_boundaries_ac07_ac08() -> None:
    payload = professional("  Ada Example  ")
    original = deepcopy(payload)
    result = group_professional_fragments([fragment(payload)])
    assert payload == original
    assert result.groups[0].key == "  Ada Example  "
    assert not hasattr(result, "person_id")
    assert not hasattr(result, "persistence")
