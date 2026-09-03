"""Behavior tests for the HRP-55 ConsolidatedPersonRecord -> PostgreSQL mapper."""

from hr_pro_platform.storage.person_mapper import map_person_record
from hr_pro_platform.transformation.bank_grouper import BankGroup, BankGroupingResult
from hr_pro_platform.transformation.fragment_contract import GroupedFragment
from hr_pro_platform.transformation.location_grouper import LocationGroup, LocationGroupingResult
from hr_pro_platform.transformation.net_grouper import NetGroup, NetGroupingResult
from hr_pro_platform.transformation.person_consolidator import consolidate_person_records
from hr_pro_platform.transformation.personal_grouper import (
    PersonalGroup,
    PersonalGroupingResult,
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


def test_complete_record_maps_every_domain_to_one_candidate_row() -> None:
    values = complete_inputs()
    result = consolidate_person_records(
        values["personal_result"],
        values["location_result"],
        values["professional_result"],
        values["bank_result"],
        values["net_result"],
    )

    mapping = map_person_record(result.records[0])

    assert mapping.status == "complete"
    assert len(mapping.employees) == 1
    assert mapping.employees[0].table == "employees"
    assert mapping.employees[0].fields == {
        "first_name": "Ada",
        "last_name": "Example",
        "sex": ["X"],
        "telephone_number": "synthetic",
        "email": "synthetic@example.test",
        "passport": "P-001",
    }
    assert mapping.locations[0].fields["full_name"] == "Ada Example"
    # location() fixture has no IPv4 key; a missing observed field must not be fabricated.
    assert "ip_v4" not in mapping.locations[0].fields
    assert mapping.professional_profiles[0].fields["company_address"] == "synthetic"
    assert mapping.bank_accounts[0].fields["iban"] == "synthetic"
    assert mapping.network_data[0].fields["ip_v4"] == "synthetic"


def test_incomplete_record_missing_domain_produces_no_candidate_rows_for_it() -> None:
    personal_result = PersonalGroupingResult(
        (PersonalGroup("P-001", "grouped", (grouped(personal(), "p"),)),), ()
    )
    bank_result = BankGroupingResult((BankGroup("P-001", "grouped", (grouped(bank(), "b"),)),), ())
    empty_location = LocationGroupingResult((), ())
    empty_professional = ProfessionalGroupingResult((), ())
    empty_net = NetGroupingResult((), ())

    result = consolidate_person_records(
        personal_result, empty_location, empty_professional, bank_result, empty_net
    )
    mapping = map_person_record(result.records[0])

    assert mapping.status == "incomplete"
    assert mapping.locations == ()
    assert mapping.professional_profiles == ()
    assert mapping.network_data == ()
    assert len(mapping.employees) == 1
    assert len(mapping.bank_accounts) == 1


def test_cross_group_ambiguity_produces_one_row_per_group_not_a_merged_row() -> None:
    personal_result = PersonalGroupingResult(
        (
            PersonalGroup("P-001", "grouped", (grouped(personal("P-001"), "p1"),)),
            PersonalGroup("P-002", "grouped", (grouped(personal("P-002"), "p2"),)),
        ),
        (),
    )
    location_result = LocationGroupingResult(
        (LocationGroup("Ada Example", "grouped", (grouped(location(), "l"),)),), ()
    )

    result = consolidate_person_records(
        personal_result,
        location_result,
        ProfessionalGroupingResult((), ()),
        BankGroupingResult((), ()),
        NetGroupingResult((), ()),
    )
    mapping = map_person_record(result.records[0])

    assert mapping.status == "ambiguous"
    assert len(mapping.employees) == 2
    assert {row.group_key for row in mapping.employees} == {"P-001", "P-002"}
    assert {row.fields["passport"] for row in mapping.employees} == {"P-001", "P-002"}


def test_intra_group_ambiguity_produces_one_row_per_fragment_sharing_group_key() -> None:
    personal_result = PersonalGroupingResult(
        (
            PersonalGroup(
                "P-001",
                "ambiguous",
                (grouped(personal(name="Ada"), "p1"), grouped(personal(name="Grace"), "p2")),
            ),
        ),
        (),
    )
    bank_result = BankGroupingResult((BankGroup("P-001", "grouped", (grouped(bank(), "b"),)),), ())

    result = consolidate_person_records(
        personal_result,
        LocationGroupingResult((), ()),
        ProfessionalGroupingResult((), ()),
        bank_result,
        NetGroupingResult((), ()),
    )
    mapping = map_person_record(result.records[0])

    assert mapping.status == "ambiguous"
    assert len(mapping.employees) == 2
    assert {row.group_key for row in mapping.employees} == {"P-001"}
    assert {row.fields["first_name"] for row in mapping.employees} == {"Ada", "Grace"}
    assert {row.source_reference for row in mapping.employees} == {"p1", "p2"}


def test_correlation_rules_and_provenance_are_preserved_unchanged() -> None:
    values = complete_inputs()
    result = consolidate_person_records(
        values["personal_result"],
        values["location_result"],
        values["professional_result"],
        values["bank_result"],
        values["net_result"],
    )
    record = result.records[0]

    mapping = map_person_record(record)

    assert mapping.correlation_rules == record.correlation_rules
    assert mapping.provenance == record.provenance


def test_no_candidate_row_carries_a_primary_key_or_employee_id() -> None:
    values = complete_inputs()
    result = consolidate_person_records(
        values["personal_result"],
        values["location_result"],
        values["professional_result"],
        values["bank_result"],
        values["net_result"],
    )
    mapping = map_person_record(result.records[0])

    all_rows = (
        mapping.employees
        + mapping.locations
        + mapping.professional_profiles
        + mapping.bank_accounts
        + mapping.network_data
    )
    for row in all_rows:
        assert "id" not in row.fields
        assert "employee_id" not in row.fields


def test_observed_field_names_translate_to_hrp25_approved_columns() -> None:
    values = complete_inputs()
    result = consolidate_person_records(
        values["personal_result"],
        values["location_result"],
        values["professional_result"],
        values["bank_result"],
        values["net_result"],
    )
    mapping = map_person_record(result.records[0])

    # telfnumber -> telephone_number, IBAN -> iban, "company address" -> company_address,
    # IPv4 -> ip_v4 (per docs/specs/HRP-25-modelo-datos.md).
    assert mapping.employees[0].fields["telephone_number"] == "synthetic"
    assert "telfnumber" not in mapping.employees[0].fields
    assert mapping.bank_accounts[0].fields["iban"] == "synthetic"
    assert "IBAN" not in mapping.bank_accounts[0].fields
    assert mapping.professional_profiles[0].fields["company_address"] == "synthetic"
    assert "company address" not in mapping.professional_profiles[0].fields
    assert mapping.network_data[0].fields["ip_v4"] == "synthetic"
    assert "IPv4" not in mapping.network_data[0].fields
