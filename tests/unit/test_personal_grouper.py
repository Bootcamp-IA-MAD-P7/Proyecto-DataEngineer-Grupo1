from copy import deepcopy

from hr_pro_platform.transformation.personal_grouper import (
    ClassifiedFragment,
    PersonalGroupingResult,
    group_personal_fragments,
)


def personal_fragment(
    passport: object = "P-001",
    *,
    name: str = "Ada",
    classification: str = "Personal",
) -> ClassifiedFragment:
    payload = {
        "name": name,
        "last_name": "Example",
        "sex": ["X"],
        "telfnumber": "000",
        "passport": passport,
        "email": f"{name.lower()}@example.test",
    }
    return ClassifiedFragment(
        payload=payload, classification=classification, source_reference="source-1"
    )


def test_same_exact_passports_share_one_personal_bucket_ac02() -> None:
    result = group_personal_fragments([personal_fragment(), personal_fragment(name="Grace")])

    assert len(result.groups) == 1
    assert result.groups[0].key == "P-001"
    assert result.groups[0].status == "ambiguous"
    assert len(result.groups[0].fragments) == 2


def test_different_exact_passports_remain_separate_ac03() -> None:
    result = group_personal_fragments([personal_fragment("P-001"), personal_fragment("P-002")])

    assert [group.key for group in result.groups] == ["P-001", "P-002"]
    assert all(group.status == "grouped" for group in result.groups)


def test_reordered_input_produces_the_same_result_ac04() -> None:
    fragments = [
        personal_fragment("P-002", name="Grace"),
        personal_fragment("P-001"),
        personal_fragment("P-002", name="Grace Two"),
    ]

    assert group_personal_fragments(fragments) == group_personal_fragments(reversed(fragments))


def test_repeated_equivalent_payload_is_retained_once_ac05() -> None:
    fragment = personal_fragment()

    result = group_personal_fragments([fragment, deepcopy(fragment), fragment])

    assert len(result.groups) == 1
    assert result.groups[0].status == "grouped"
    assert len(result.groups[0].fragments) == 1


def test_missing_passport_is_unsupported_and_does_not_use_fallback_ac06() -> None:
    fragment = personal_fragment()
    del fragment.payload["passport"]  # type: ignore[index]

    result = group_personal_fragments([fragment])

    assert result.groups == ()
    assert len(result.unresolved) == 1
    assert result.unresolved[0].status == "unsupported"


def test_empty_null_and_non_string_passports_are_uncorrelated_ac06() -> None:
    result = group_personal_fragments(
        [personal_fragment(""), personal_fragment(None), personal_fragment(["P-001"])]
    )

    assert result.groups == ()
    assert [item.status for item in result.unresolved] == [
        "uncorrelated",
        "uncorrelated",
        "uncorrelated",
    ]
    assert all(item.reason == "passport_unusable" for item in result.unresolved)


def test_distinct_same_passport_evidence_is_ambiguous_ac07() -> None:
    result = group_personal_fragments(
        [personal_fragment(name="Ada"), personal_fragment(name="Grace")]
    )

    assert result.groups[0].status == "ambiguous"
    assert len(result.groups[0].fragments) == 2


def test_non_personal_and_malformed_input_are_unsupported_ac08() -> None:
    result = group_personal_fragments(
        [
            personal_fragment(classification="Bank"),
            ClassifiedFragment(
                payload=["not an object"], classification="Personal", source_reference="source-1"
            ),
        ]
    )

    assert result.groups == ()
    assert len(result.unresolved) == 2
    assert all(item.status == "unsupported" for item in result.unresolved)


def test_passport_is_not_trimmed_or_case_folded_ac03_ac10() -> None:
    result = group_personal_fragments(
        [personal_fragment("P-001"), personal_fragment(" P-001 "), personal_fragment("p-001")]
    )

    assert [group.key for group in result.groups] == [" P-001 ", "P-001", "p-001"]


def test_grouping_does_not_mutate_caller_owned_inputs_ac09() -> None:
    fragment = personal_fragment()
    original = deepcopy(fragment)

    group_personal_fragments([fragment])

    assert fragment == original


def test_personal_grouping_returns_the_declared_result_type_ac01() -> None:
    result = group_personal_fragments([personal_fragment()])

    assert isinstance(result, PersonalGroupingResult)
