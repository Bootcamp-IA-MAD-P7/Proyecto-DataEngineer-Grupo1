"""Behavior tests for HRP-46 Location operational grouping."""

from copy import deepcopy

from hr_pro_platform.transformation.classifier import UNKNOWN
from hr_pro_platform.transformation.location_grouper import (
    ClassifiedFragment,
    JSONValue,
    group_location_fragments,
)


def location(
    fullname: JSONValue,
    city: JSONValue = "synthetic",
    address: JSONValue = "synthetic",
) -> dict[str, JSONValue]:
    return {"fullname": fullname, "city": city, "address": address}


def fragment(payload: JSONValue, classification: str = "Location") -> ClassifiedFragment:
    return ClassifiedFragment(payload=payload, classification=classification)


def test_valid_location_is_grouped_by_exact_fullname_ac01() -> None:
    payload = location("  Example Person  ")
    result = group_location_fragments([fragment(payload)])

    assert len(result.groups) == 1
    assert result.groups[0].key == "  Example Person  "
    assert result.groups[0].status == "grouped"
    assert result.groups[0].fragments == (payload,)


def test_equal_and_different_fullnames_define_local_groups_without_identity_ac02() -> None:
    result = group_location_fragments(
        [
            fragment(location("Ada Example", "one")),
            fragment(location("Ada Example", "two")),
            fragment(location("Bob Example")),
        ]
    )

    assert [group.key for group in result.groups] == ["Ada Example", "Bob Example"]
    assert result.groups[0].status == "ambiguous"
    assert not hasattr(result.groups[0], "person_id")


def test_duplicate_payloads_and_input_order_are_deterministic_ac03() -> None:
    first = [fragment(location("Ada Example", "one")), fragment(location("Bob Example"))]
    second = list(reversed(first + [fragment(location("Ada Example", "one"))]))

    assert group_location_fragments(first) == group_location_fragments(second)
    assert len(group_location_fragments(second).groups[0].fragments) == 1


def test_missing_empty_and_non_string_fullname_are_uncorrelated_ac04() -> None:
    result = group_location_fragments(
        [
            fragment(location(None)),
            fragment(location("")),
            fragment(location(42)),
        ]
    )

    assert len(result.unresolved) == 3
    assert all(item.status == "uncorrelated" for item in result.unresolved)
    assert all(item.reason == "fullname_unusable" for item in result.unresolved)


def test_structurally_missing_fullname_is_unsupported_ac04() -> None:
    result = group_location_fragments([fragment({"city": "synthetic", "address": "synthetic"})])

    assert result.groups == ()
    assert result.unresolved[0].status == "unsupported"
    assert result.unresolved[0].reason == "classification_mismatch"


def test_conflicting_same_key_values_are_preserved_as_ambiguous_ac05() -> None:
    first = location("Ada Example", "one", "first")
    second = location("Ada Example", "two", "second")

    result = group_location_fragments([fragment(first), fragment(second)])

    assert result.groups[0].status == "ambiguous"
    assert result.groups[0].fragments == (first, second)


def test_unsupported_classification_or_invalid_upstream_input_is_explicit_ac06() -> None:
    result = group_location_fragments(
        [
            fragment(
                {
                    "name": "synthetic",
                    "last_name": "synthetic",
                    "sex": [],
                    "telfnumber": "synthetic",
                    "passport": "synthetic",
                    "email": "synthetic",
                },
                "Personal",
            ),
            fragment({}, "Location"),
            fragment(location("synthetic"), UNKNOWN),
        ]
    )

    assert [item.status for item in result.unresolved] == [
        "unsupported",
        "unsupported",
        "unsupported",
    ]
    assert {item.reason for item in result.unresolved} == {
        "classification_mismatch",
        "not_location_fragment",
        "unsupported_classification",
    }


def test_grouping_does_not_mutate_payload_or_classification_context_ac07() -> None:
    payload = location("  Ada Example  ", "synthetic", "synthetic")
    original = deepcopy(payload)
    input_fragment = fragment(payload)

    group_location_fragments([input_fragment])

    assert payload == original
    assert input_fragment == fragment(original)


def test_grouping_has_no_fallback_or_global_identity_and_keeps_persistence_outside_scope_ac08() -> (
    None
):
    result = group_location_fragments(
        [
            fragment(location("Ada Example", address="same-address")),
            fragment(location("Bob Example", address="same-address")),
        ]
    )

    assert [group.key for group in result.groups] == ["Ada Example", "Bob Example"]
    assert result.groups[0].fragments[0]["fullname"] == "Ada Example"
    assert not hasattr(result, "person_id")
    assert not hasattr(result.groups[0], "employee_id")
