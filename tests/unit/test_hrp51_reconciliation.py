"""Executable HRP-51 recomputation and duplicate-behavior tests."""

from copy import deepcopy

from hr_pro_platform.transformation.bank_grouper import group_bank_fragments
from hr_pro_platform.transformation.fragment_contract import (
    ClassifiedFragment,
    JSONValue,
    UnresolvedFragment,
)
from hr_pro_platform.transformation.location_grouper import group_location_fragments
from hr_pro_platform.transformation.net_grouper import group_net_fragments
from hr_pro_platform.transformation.person_consolidator import (
    ConsolidationResult,
    consolidate_person_records,
)
from hr_pro_platform.transformation.personal_grouper import (
    PersonalGroupingResult,
    group_personal_fragments,
)
from hr_pro_platform.transformation.professional_grouper import group_professional_fragments


def fragment(payload: JSONValue, classification: str, source: str) -> ClassifiedFragment:
    return ClassifiedFragment(
        payload=payload, classification=classification, source_reference=source
    )


def personal(name: str = "Ada", passport: str = "P-001") -> dict[str, JSONValue]:
    return {
        "name": name,
        "last_name": "Example",
        "sex": ["X"],
        "telfnumber": "synthetic",
        "passport": passport,
        "email": "synthetic@example.test",
    }


def location() -> dict[str, JSONValue]:
    return {"fullname": "Ada Example", "city": "synthetic", "address": "A-1"}


def professional() -> dict[str, JSONValue]:
    return {
        "fullname": "Ada Example",
        "company": "synthetic",
        "company address": "synthetic",
        "company_telfnumber": "synthetic",
        "company_email": "synthetic@example.test",
        "job": "synthetic",
    }


def bank() -> dict[str, JSONValue]:
    return {"passport": "P-001", "IBAN": "synthetic", "salary": "synthetic"}


def net() -> dict[str, JSONValue]:
    return {"address": "A-1", "IPv4": "synthetic"}


def consolidate(
    personal_result: PersonalGroupingResult,
    *,
    include_location: bool = False,
    include_professional: bool = False,
    include_bank: bool = False,
    include_net: bool = False,
) -> ConsolidationResult:
    return consolidate_person_records(
        personal_result,
        group_location_fragments(
            [fragment(location(), "Location", "location-1")] if include_location else []
        ),
        group_professional_fragments(
            [fragment(professional(), "Professional", "professional-1")]
            if include_professional
            else []
        ),
        group_bank_fragments([fragment(bank(), "Bank", "bank-1")] if include_bank else []),
        group_net_fragments([fragment(net(), "Net", "net-1")] if include_net else []),
    )


def test_exact_pair_replay_is_deduplicated_end_to_end_ac05() -> None:
    source_fragment = fragment(personal(), "Personal", "personal-1")

    original = consolidate(group_personal_fragments([source_fragment]))
    repeated = consolidate(group_personal_fragments([source_fragment, deepcopy(source_fragment)]))

    assert repeated == original
    assert len(repeated.records[0].domains["personal"].groups[0].fragments) == 1  # type: ignore[union-attr]
    assert repeated.records[0].provenance == ("personal-1",)


def test_different_source_reference_is_retained_and_ambiguous_end_to_end_ac06() -> None:
    payload = personal()

    grouped = group_personal_fragments(
        [fragment(payload, "Personal", "personal-1"), fragment(payload, "Personal", "personal-2")]
    )
    result = consolidate(grouped)

    contribution = result.records[0].domains["personal"]
    assert result.records[0].status == "ambiguous"
    assert contribution is not None
    assert len(contribution.groups) == 1
    assert [item.source_reference for item in contribution.groups[0].fragments] == [
        "personal-1",
        "personal-2",
    ]
    assert [item.payload for item in contribution.groups[0].fragments] == [payload, payload]


def test_recomputation_is_order_independent_and_preserves_provenance_ac01_ac02_ac09() -> None:
    fragments = [
        fragment(personal("Ada", "P-001"), "Personal", "personal-1"),
        fragment(personal("Grace", "P-002"), "Personal", "personal-2"),
        fragment(personal("Ivy", "P-003"), "Personal", "personal-3"),
        fragment(personal("Leo", "P-004"), "Personal", "personal-4"),
    ]
    first_personal = group_personal_fragments(fragments)
    snapshot = deepcopy(first_personal)
    first = consolidate(first_personal)
    second = consolidate(group_personal_fragments([fragments[index] for index in (2, 0, 3, 1)]))
    third = consolidate(group_personal_fragments([fragments[index] for index in (1, 3, 0, 2)]))

    assert first == second == third
    assert first_personal == snapshot
    assert [record.provenance for record in first.records] == [
        ("personal-1",),
        ("personal-2",),
        ("personal-3",),
        ("personal-4",),
    ]


def test_incomplete_component_becomes_complete_after_valid_evidence_ac03() -> None:
    personal_result = group_personal_fragments([fragment(personal(), "Personal", "personal-1")])

    incomplete = consolidate(personal_result, include_bank=True)
    complete = consolidate(
        personal_result,
        include_location=True,
        include_professional=True,
        include_bank=True,
        include_net=True,
    )

    assert incomplete.records[0].status == "incomplete"
    assert complete.records[0].status == "complete"


def test_incomplete_component_becomes_ambiguous_after_conflicting_evidence_ac04_ac08() -> None:
    initial_personal = group_personal_fragments(
        [fragment(personal("Ada"), "Personal", "personal-1")]
    )
    initial_snapshot = deepcopy(initial_personal)
    incomplete = consolidate(initial_personal, include_bank=True)
    incomplete_snapshot = deepcopy(incomplete)

    expanded_personal = group_personal_fragments(
        [
            fragment(personal("Ada"), "Personal", "personal-1"),
            fragment(personal("Grace"), "Personal", "personal-2"),
        ]
    )
    consolidated = consolidate(expanded_personal, include_bank=True)

    assert incomplete.records[0].status == "incomplete"
    assert consolidated.records[0].status == "ambiguous"
    assert initial_personal == initial_snapshot
    assert incomplete == incomplete_snapshot
    assert len(consolidated.records[0].domains["personal"].groups[0].fragments) == 2  # type: ignore[union-attr]
    assert {
        item.source_reference for item in consolidated.records[0].domains["personal"].fragments
    } == {  # type: ignore[union-attr]
        "personal-1",
        "personal-2",
    }


def test_domain_group_boundaries_are_preserved_ac09() -> None:
    valid = group_personal_fragments([fragment(personal(), "Personal", "personal-1")])
    result = consolidate(valid)

    assert [group.key for group in result.records[0].domains["personal"].groups] == ["P-001"]  # type: ignore[union-attr]
    assert (
        result.records[0].domains["personal"].groups[0].fragments[0].source_reference
        == "personal-1"
    )  # type: ignore[union-attr]


def test_conflicting_values_do_not_select_a_recency_winner_ac07_ac08() -> None:
    first = [
        fragment(personal("Ada"), "Personal", "personal-1"),
        fragment(personal("Grace"), "Personal", "personal-2"),
    ]
    second = [first[1], first[0]]

    first_result = consolidate(group_personal_fragments(first))
    second_result = consolidate(group_personal_fragments(second))

    assert first_result == second_result
    assert first_result.records[0].status == "ambiguous"
    assert {
        item.payload["name"]
        for item in first_result.records[0].domains["personal"].fragments  # type: ignore[union-attr]
    } == {"Ada", "Grace"}


def test_unresolved_material_remains_explicit_at_consolidation_boundary_ac10() -> None:
    unresolved = group_personal_fragments(
        [
            ClassifiedFragment(
                payload={"name": "incomplete"},
                classification="Personal",
                source_reference="unresolved-1",
            )
        ]
    )

    result = consolidate_person_records(
        unresolved,
        group_location_fragments([]),
        group_professional_fragments([]),
        group_bank_fragments([]),
        group_net_fragments([]),
    )

    assert isinstance(unresolved.unresolved[0], UnresolvedFragment)
    assert result.records == ()
    assert result.unresolved[0].source_reference == "unresolved-1"
    assert result.unresolved[0].context == "Personal"


def test_recomputation_does_not_mutate_grouped_or_unresolved_inputs_ac01_ac10() -> None:
    personal_result = group_personal_fragments([fragment(personal(), "Personal", "personal-1")])
    location_result = group_location_fragments([fragment(location(), "Location", "location-1")])
    professional_result = group_professional_fragments(
        [fragment(professional(), "Professional", "professional-1")]
    )
    bank_result = group_bank_fragments([fragment(bank(), "Bank", "bank-1")])
    net_result = group_net_fragments([fragment(net(), "Net", "net-1")])
    unresolved_result = group_personal_fragments(
        [
            ClassifiedFragment(
                payload={"name": "incomplete"},
                classification="Personal",
                source_reference="unresolved-1",
            )
        ]
    )
    snapshots = tuple(
        deepcopy(value)
        for value in (
            personal_result,
            location_result,
            professional_result,
            bank_result,
            net_result,
            unresolved_result,
        )
    )

    consolidate_person_records(
        personal_result,
        location_result,
        professional_result,
        bank_result,
        net_result,
    )
    consolidate_person_records(
        unresolved_result,
        group_location_fragments([]),
        group_professional_fragments([]),
        group_bank_fragments([]),
        group_net_fragments([]),
    )

    assert (
        personal_result,
        location_result,
        professional_result,
        bank_result,
        net_result,
        unresolved_result,
    ) == snapshots
