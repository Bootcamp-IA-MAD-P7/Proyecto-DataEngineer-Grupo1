"""Behavior tests for HRP-49 Net operational grouping."""

from copy import deepcopy

from hr_pro_platform.transformation.classifier import UNKNOWN
from hr_pro_platform.transformation.net_grouper import (
    ClassifiedFragment,
    JSONValue,
    group_net_fragments,
)


def net(address: JSONValue, ipv4: JSONValue = "synthetic") -> dict[str, JSONValue]:
    return {"address": address, "IPv4": ipv4}


def fragment(
    payload: JSONValue, classification: str = "Net", source: str = "source-1"
) -> ClassifiedFragment:
    return ClassifiedFragment(
        payload=payload, classification=classification, source_reference=source
    )


def test_valid_net_payload_is_retained_ac01() -> None:
    payload = net("Net address 001")
    result = group_net_fragments([fragment(payload)])
    assert result.groups[0].key == "Net address 001"
    assert result.groups[0].fragments[0].payload == payload
    assert result.groups[0].fragments[0].source_reference == "source-1"


def test_same_and_different_addresses_define_domain_local_groups_ac02() -> None:
    result = group_net_fragments([fragment(net("A")), fragment(net("B")), fragment(net("A"))])
    assert [group.key for group in result.groups] == ["A", "B"]
    assert not hasattr(result.groups[0], "person_id")


def test_duplicate_net_payloads_are_deterministic_ac03() -> None:
    first = [fragment(net("A")), fragment(net("B"))]
    second = list(reversed(first + [fragment(net("A"))]))
    assert group_net_fragments(first) == group_net_fragments(second)
    assert len(group_net_fragments(second).groups[0].fragments) == 1


def test_missing_net_address_is_unsupported_ac04() -> None:
    result = group_net_fragments([fragment({"IPv4": "synthetic"})])
    assert result.unresolved[0].status == "unsupported"
    assert result.unresolved[0].reason == "classification_mismatch"


def test_unusable_net_address_is_uncorrelated_ac04() -> None:
    result = group_net_fragments([fragment(net("")), fragment(net(None)), fragment(net(42))])
    assert len(result.unresolved) == 3
    assert all(item.status == "uncorrelated" for item in result.unresolved)


def test_distinct_same_address_evidence_is_ambiguous_ac05() -> None:
    first = net("same", "one")
    second = net("same", "two")
    result = group_net_fragments([fragment(first), fragment(second)])
    assert result.groups[0].status == "ambiguous"
    assert len(result.groups[0].fragments) == 2
    assert [item.payload for item in result.groups[0].fragments] == [first, second]


def test_unsupported_net_input_is_explicit_ac06() -> None:
    result = group_net_fragments(
        [
            fragment({}, UNKNOWN),
            fragment(net("A"), "Bank"),
            fragment([]),
            fragment({"address": "A", "IPv4": "x", "extra": "unsupported"}),
        ]
    )
    assert len(result.unresolved) == 4
    assert all(item.status == "unsupported" for item in result.unresolved)


def test_net_grouping_preserves_payload_and_context_ac07() -> None:
    payload = net("  A  ")
    original = deepcopy(payload)
    context = fragment(payload)
    result = group_net_fragments([context])
    assert payload == original
    assert context == fragment(payload)
    assert result.groups[0].key == "  A  "


def test_net_grouping_has_no_normalization_fallback_or_identity_ac08() -> None:
    result = group_net_fragments(
        [
            fragment(
                net("a"),
            ),
            fragment(net("A")),
            fragment(net("fallback", "same")),
        ]
    )
    assert [group.key for group in result.groups] == ["A", "a", "fallback"]
    assert not hasattr(result, "person_id")
