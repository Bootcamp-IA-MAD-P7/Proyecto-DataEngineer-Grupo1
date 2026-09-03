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

# Every field below uses a distinguishable synthetic value (not a repeated
# "synthetic" placeholder) so a misrouted mapping (e.g. city swapped with
# address, or one row's fields attached to another row's group_key/source
# reference) fails an exact-equality assertion instead of passing by luck.


def personal(passport: str = "P-001", name: str = "Ada") -> dict[str, object]:
    return {
        "name": name,
        "last_name": "Example",
        "sex": ["X"],
        "telfnumber": "+34-600-000-001",
        "passport": passport,
        "email": "ada.example@example.test",
    }


def location(fullname: str = "Ada Example", address: str = "A-1") -> dict[str, object]:
    return {"fullname": fullname, "city": "Springfield", "address": address}


def professional(fullname: str = "Ada Example") -> dict[str, object]:
    return {
        "fullname": fullname,
        "company": "Acme Corp",
        "company address": "123 Acme Avenue",
        "company_telfnumber": "+34-900-000-002",
        "company_email": "ada.example@acme.test",
        "job": "Engineer",
    }


def bank(passport: str = "P-001") -> dict[str, object]:
    return {"passport": passport, "IBAN": "ES00-0000-0000-0000", "salary": "50000"}


def net(address: str = "A-1") -> dict[str, object]:
    return {"address": address, "IPv4": "10.0.0.1"}


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


def test_complete_record_maps_every_domain_to_one_full_candidate_row() -> None:
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
    assert mapping.employees[0].group_key == "P-001"
    assert mapping.employees[0].source_reference == "p"
    assert mapping.employees[0].fields == {
        "first_name": "Ada",
        "last_name": "Example",
        "sex": ["X"],
        "telephone_number": "+34-600-000-001",
        "email": "ada.example@example.test",
        "passport": "P-001",
    }

    assert len(mapping.locations) == 1
    assert mapping.locations[0].table == "locations"
    assert mapping.locations[0].group_key == "Ada Example"
    assert mapping.locations[0].source_reference == "l"
    assert mapping.locations[0].fields == {
        "full_name": "Ada Example",
        "city": "Springfield",
        "address": "A-1",
    }  # location() fixture has no IPv4 key; ip_v4 must not be fabricated.

    assert len(mapping.professional_profiles) == 1
    assert mapping.professional_profiles[0].table == "professional_profiles"
    assert mapping.professional_profiles[0].group_key == "Ada Example"
    assert mapping.professional_profiles[0].source_reference == "w"
    assert mapping.professional_profiles[0].fields == {
        "full_name": "Ada Example",
        "company": "Acme Corp",
        "company_address": "123 Acme Avenue",
        "company_telephone_number": "+34-900-000-002",
        "company_email": "ada.example@acme.test",
        "job": "Engineer",
    }

    assert len(mapping.bank_accounts) == 1
    assert mapping.bank_accounts[0].table == "bank_accounts"
    assert mapping.bank_accounts[0].group_key == "P-001"
    assert mapping.bank_accounts[0].source_reference == "b"
    assert mapping.bank_accounts[0].fields == {
        "iban": "ES00-0000-0000-0000",
        "passport": "P-001",
        "salary": "50000",
    }

    assert len(mapping.network_data) == 1
    assert mapping.network_data[0].table == "network_data"
    assert mapping.network_data[0].group_key == "A-1"
    assert mapping.network_data[0].source_reference == "n"
    assert mapping.network_data[0].fields == {"ip_v4": "10.0.0.1"}


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


def test_cross_group_ambiguity_keeps_each_groups_fields_correctly_paired() -> None:
    """Two distinct PersonalGroups joined transitively via Location (HRP-96 shape).

    Both personal fragments must keep the same `name`/`last_name` (default
    "Ada Example") because that is what makes them both match the Location
    group's `fullname` key via the `personal_location_fullname` edge and
    therefore land in one ambiguous component — only `passport` (the
    Personal group's own local key) and the source reference distinguish the
    two groups. Builds a mapping keyed by group_key from the mapper's actual
    output and compares it to the exact expected pairing, so a bug that swaps
    one row's fields/source_reference with another row's group_key would fail.
    """
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

    by_group_key = {row.group_key: row for row in mapping.employees}
    assert by_group_key.keys() == {"P-001", "P-002"}
    assert by_group_key["P-001"].source_reference == "p1"
    assert by_group_key["P-001"].fields["passport"] == "P-001"
    assert by_group_key["P-002"].source_reference == "p2"
    assert by_group_key["P-002"].fields["passport"] == "P-002"


def test_intra_group_ambiguity_keeps_each_fragments_fields_correctly_paired() -> None:
    """One PersonalGroup already ambiguous (two conflicting fragments under one key).

    Builds a mapping keyed by source_reference and compares it to the exact
    expected pairing, so a bug that swaps one fragment's name with the
    other's source_reference would fail.
    """
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

    by_source_reference = {row.source_reference: row for row in mapping.employees}
    assert by_source_reference.keys() == {"p1", "p2"}
    assert by_source_reference["p1"].fields["first_name"] == "Ada"
    assert by_source_reference["p2"].fields["first_name"] == "Grace"


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
