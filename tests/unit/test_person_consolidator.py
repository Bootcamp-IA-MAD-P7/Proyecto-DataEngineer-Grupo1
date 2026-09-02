"""Behavior tests for HRP-50 consolidated operational records."""

from copy import deepcopy

import pytest

from hr_pro_platform.transformation.bank_grouper import BankGroup, BankGroupingResult
from hr_pro_platform.transformation.fragment_contract import GroupedFragment
from hr_pro_platform.transformation.location_grouper import LocationGroup, LocationGroupingResult
from hr_pro_platform.transformation.net_grouper import NetGroup, NetGroupingResult
from hr_pro_platform.transformation.person_consolidator import (
    ConsolidationResult,
    consolidate_person_records,
)
from hr_pro_platform.transformation.personal_grouper import (
    PersonalGroup,
    PersonalGroupingResult,
)
from hr_pro_platform.transformation.personal_grouper import (
    UnresolvedFragment as PersonalUnresolved,
)
from hr_pro_platform.transformation.professional_grouper import (
    ProfessionalGroup,
    ProfessionalGroupingResult,
)


def personal(passport: str = "P-001", name: str = "Ada") -> dict[str, object]:
    return {
        "name": name,
        "last_name": "Example",
        "sex": ["X"],
        "telfnumber": "synthetic",
        "passport": passport,
        "email": "synthetic@example.test",
    }


def location(fullname: str = "Ada Example", address: str = "A-1") -> dict[str, object]:
    return {"fullname": fullname, "city": "synthetic", "address": address}


def professional(fullname: str = "Ada Example") -> dict[str, object]:
    return {
        "fullname": fullname,
        "company": "synthetic",
        "company address": "synthetic",
        "company_telfnumber": "synthetic",
        "company_email": "synthetic@example.test",
        "job": "synthetic",
    }


def bank(passport: str = "P-001") -> dict[str, object]:
    return {"passport": passport, "IBAN": "synthetic", "salary": "synthetic"}


def net(address: str = "A-1") -> dict[str, object]:
    return {"address": address, "IPv4": "synthetic"}


def grouped(payload: dict[str, object], source: str) -> GroupedFragment:
    return GroupedFragment(payload=payload, source_reference=source)


def inputs(
    *,
    personal_result: PersonalGroupingResult | None = None,
    location_result: LocationGroupingResult | None = None,
    professional_result: ProfessionalGroupingResult | None = None,
    bank_result: BankGroupingResult | None = None,
    net_result: NetGroupingResult | None = None,
) -> ConsolidationResult:
    return consolidate_person_records(
        personal_result or PersonalGroupingResult((), ()),
        location_result or LocationGroupingResult((), ()),
        professional_result or ProfessionalGroupingResult((), ()),
        bank_result or BankGroupingResult((), ()),
        net_result or NetGroupingResult((), ()),
    )


def complete_inputs() -> dict[str, object]:
    return {
        "personal_result": PersonalGroupingResult(
            (PersonalGroup("P-001", "grouped", (grouped(personal(), "p"),)),), ()
        ),
        "location_result": LocationGroupingResult(
            (LocationGroup("Ada Example", "grouped", (grouped(location(), "l"),)),), ()
        ),
        "professional_result": ProfessionalGroupingResult(
            (ProfessionalGroup("Ada Example", "grouped", (grouped(professional(), "w"),)),), ()
        ),
        "bank_result": BankGroupingResult(
            (BankGroup("P-001", "grouped", (grouped(bank(), "b"),)),), ()
        ),
        "net_result": NetGroupingResult((NetGroup("A-1", "grouped", (grouped(net(), "n"),)),), ()),
    }


def test_complete_five_domain_chain_produces_one_record_ac01() -> None:
    result = inputs(**complete_inputs())

    assert len(result.records) == 1
    assert result.records[0].status == "complete"
    assert set(result.records[0].domains) == {
        "personal",
        "location",
        "professional",
        "bank",
        "net",
    }
    assert result.records[0].correlation_rules == (
        "location_net_address",
        "location_professional_fullname",
        "personal_bank_passport",
        "personal_location_fullname",
    )
    assert result.records[0].provenance == ("b", "l", "n", "p", "w")


def test_personal_and_bank_form_incomplete_component_ac02() -> None:
    result = inputs(
        personal_result=PersonalGroupingResult(
            (PersonalGroup("P-001", "grouped", (grouped(personal(), "p"),)),), ()
        ),
        bank_result=BankGroupingResult(
            (BankGroup("P-001", "grouped", (grouped(bank(), "b"),)),), ()
        ),
    )

    assert len(result.records) == 1
    assert result.records[0].status == "incomplete"
    assert result.records[0].domains["location"] is None
    assert result.records[0].correlation_rules == ("personal_bank_passport",)


def test_location_professional_and_net_form_incomplete_component_ac03() -> None:
    values = complete_inputs()
    result = inputs(
        location_result=values["location_result"],
        professional_result=values["professional_result"],
        net_result=values["net_result"],
    )

    assert len(result.records) == 1
    assert result.records[0].status == "incomplete"
    assert result.records[0].domains["personal"] is None
    assert result.records[0].correlation_rules == (
        "location_net_address",
        "location_professional_fullname",
    )


def test_personal_location_bridge_joins_transitively_ac04() -> None:
    values = complete_inputs()
    result = inputs(
        personal_result=values["personal_result"],
        location_result=values["location_result"],
        professional_result=values["professional_result"],
        net_result=values["net_result"],
        bank_result=values["bank_result"],
    )

    assert len(result.records) == 1
    assert "personal_location_fullname" in result.records[0].correlation_rules


def test_missing_domains_are_explicit_and_unrelated_components_stay_separate_ac05_ac06() -> None:
    result = inputs(
        personal_result=PersonalGroupingResult(
            (
                PersonalGroup("P-001", "grouped", (grouped(personal("P-001"), "p1"),)),
                PersonalGroup("P-002", "grouped", (grouped(personal("P-002", "Bob"), "p2"),)),
            ),
            (),
        )
    )

    assert len(result.records) == 2
    assert all(record.status == "incomplete" for record in result.records)
    assert all(record.domains["bank"] is None for record in result.records)


@pytest.mark.parametrize("fullname", ["ada Example", "Ada  Example", "Áda Example"])
def test_exact_mismatch_does_not_normalize_ac07(fullname: str) -> None:
    result = inputs(
        personal_result=PersonalGroupingResult(
            (PersonalGroup("P-001", "grouped", (grouped(personal(), "p"),)),), ()
        ),
        location_result=LocationGroupingResult(
            (LocationGroup(fullname, "grouped", (grouped(location(fullname), "l"),)),), ()
        ),
    )

    assert len(result.records) == 2
    assert all(record.correlation_rules == () for record in result.records)


def test_ambiguous_component_is_preserved_without_resolution_ac09() -> None:
    result = inputs(
        personal_result=PersonalGroupingResult(
            (
                PersonalGroup(
                    "P-001",
                    "ambiguous",
                    (grouped(personal(name="Ada"), "p1"), grouped(personal(name="Grace"), "p2")),
                ),
            ),
            (),
        ),
        bank_result=BankGroupingResult(
            (BankGroup("P-001", "grouped", (grouped(bank(), "b"),)),), ()
        ),
    )

    assert result.records[0].status == "ambiguous"
    assert len(result.records[0].domains["personal"].fragments) == 2  # type: ignore[union-attr]
    assert result.records[0].provenance == ("b", "p1", "p2")


def test_unresolved_input_is_kept_outside_records_ac10() -> None:
    unresolved = PersonalUnresolved(
        status="uncorrelated",
        payload=personal(""),
        classification="Personal",
        source_reference="p-unresolved",
        reason="passport_unusable",
    )
    result = inputs(personal_result=PersonalGroupingResult((), (unresolved,)))

    assert result.records == ()
    assert result.unresolved[0].source_reference == "p-unresolved"
    assert result.unresolved[0].reason == "passport_unusable"


def test_unresolved_source_references_have_deterministic_order_ac13() -> None:
    first = PersonalUnresolved(
        status="uncorrelated",
        payload=personal(""),
        classification="Personal",
        source_reference="source-b",
        reason="passport_unusable",
    )
    second = PersonalUnresolved(
        status="uncorrelated",
        payload=personal(""),
        classification="Personal",
        source_reference="source-a",
        reason="passport_unusable",
    )

    result = inputs(personal_result=PersonalGroupingResult((), (first, second)))

    assert [item.source_reference for item in result.unresolved] == ["source-a", "source-b"]


def test_same_logical_grouped_input_is_deterministic_and_immutable_ac11_ac14() -> None:
    values = complete_inputs()
    snapshot = deepcopy(values)
    first = inputs(**values)
    second = inputs(**dict(reversed(tuple(values.items()))))

    assert first == second
    assert values == snapshot
