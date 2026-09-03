"""HRP-60 integration tests: grouped/consolidated data persists correctly.

Every existing test in ``test_person_repository.py`` hand-builds a
``PersonRecordMapping``/``CandidateRow`` and calls ``PersonRepository``
directly, so none of them exercise the grouping (HRP-46-49/61) or
consolidation (HRP-50) stages. These tests run synthetic, minimized,
non-PII ``ClassifiedFragment`` input through the real, unmodified
production pipeline -- domain groupers -> ``consolidate_person_records`` ->
``map_person_record`` -> ``PersonRepository.insert_mapping`` -- and verify
the resulting rows against a real PostgreSQL container. See
docs/specs/HRP-60-grouped-data-persistence-verification.md.

Every correlation-based assertion below is scoped to "these fragments were
grouped through an approved ADR-0006 exact edge"; none claims real-world
identity, per ADR-0006's documented limitations.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence

import psycopg
import pytest


@pytest.fixture
def live_connection() -> Iterator[psycopg.Connection[tuple[object, ...]]]:
    try:
        from hr_pro_platform.storage.config import (
            POSTGRES_DB,
            POSTGRES_HOST,
            POSTGRES_PASSWORD,
            POSTGRES_PORT,
            POSTGRES_USER,
        )
    except OSError:
        pytest.skip("PostgreSQL environment variables are not configured (.env missing?).")

    try:
        connection = psycopg.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            connect_timeout=2,
        )
    except psycopg.OperationalError:
        pytest.skip(
            "PostgreSQL is not reachable; "
            "start it with `docker compose -f infra/compose.dev.yml up -d postgres`."
        )
    try:
        yield connection
    finally:
        connection.close()


def _personal(name: str, last_name: str, passport: str, source_reference: str):
    from hr_pro_platform.transformation.fragment_contract import ClassifiedFragment

    return ClassifiedFragment(
        payload={
            "name": name,
            "last_name": last_name,
            "sex": ["X"],
            "telfnumber": "000-000-0000",
            "passport": passport,
            "email": f"{name.lower()}.{last_name.lower()}@hrp60.test",
        },
        classification="Personal",
        source_reference=source_reference,
    )


def _location(fullname: str, city: str, address: str, source_reference: str):
    from hr_pro_platform.transformation.fragment_contract import ClassifiedFragment

    return ClassifiedFragment(
        payload={"fullname": fullname, "city": city, "address": address},
        classification="Location",
        source_reference=source_reference,
    )


def _professional(fullname: str, job: str, source_reference: str):
    from hr_pro_platform.transformation.fragment_contract import ClassifiedFragment

    return ClassifiedFragment(
        payload={
            "fullname": fullname,
            "company": "HRP60 Test Corp",
            "company address": "1 Test Corp Way",
            "company_telfnumber": "000-111-0000",
            "company_email": "hr@hrp60testcorp.test",
            "job": job,
        },
        classification="Professional",
        source_reference=source_reference,
    )


def _bank(passport: str, iban: str, source_reference: str):
    from hr_pro_platform.transformation.fragment_contract import ClassifiedFragment

    return ClassifiedFragment(
        payload={"passport": passport, "IBAN": iban, "salary": "50000"},
        classification="Bank",
        source_reference=source_reference,
    )


def _net(address: str, ipv4: str, source_reference: str):
    from hr_pro_platform.transformation.fragment_contract import ClassifiedFragment

    return ClassifiedFragment(
        payload={"address": address, "IPv4": ipv4},
        classification="Net",
        source_reference=source_reference,
    )


def _run_pipeline(fragments: Sequence[object]) -> list[object]:
    """Run the real grouping -> consolidation -> mapping pipeline.

    Orchestration only -- every function called is unmodified production
    code (HRP-46-49/61/50/55). Returns one ``PersonRecordMapping`` per
    consolidated component; unresolved input is discarded on purpose (no
    test below relies on it).
    """

    from hr_pro_platform.storage.person_mapper import map_person_record
    from hr_pro_platform.transformation.bank_grouper import group_bank_fragments
    from hr_pro_platform.transformation.location_grouper import group_location_fragments
    from hr_pro_platform.transformation.net_grouper import group_net_fragments
    from hr_pro_platform.transformation.person_consolidator import consolidate_person_records
    from hr_pro_platform.transformation.personal_grouper import group_personal_fragments
    from hr_pro_platform.transformation.professional_grouper import group_professional_fragments

    by_domain: dict[str, list[object]] = {
        "Personal": [],
        "Location": [],
        "Professional": [],
        "Bank": [],
        "Net": [],
    }
    for fragment in fragments:
        by_domain[fragment.classification].append(fragment)  # type: ignore[attr-defined]

    consolidation = consolidate_person_records(
        group_personal_fragments(by_domain["Personal"]),
        group_location_fragments(by_domain["Location"]),
        group_professional_fragments(by_domain["Professional"]),
        group_bank_fragments(by_domain["Bank"]),
        group_net_fragments(by_domain["Net"]),
    )
    return [map_person_record(record) for record in consolidation.records]


def _cleanup(
    connection: psycopg.Connection[tuple[object, ...]], employee_ids: Sequence[int]
) -> None:
    with connection.cursor() as cursor:
        for employee_id in employee_ids:
            cursor.execute("DELETE FROM processing_audit WHERE employee_id = %s", (employee_id,))
            cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
    connection.commit()


def test_complete_five_domain_component_persists_correctly_end_to_end(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.storage.person_repository import PersonRepository
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    schema_client = PostgresSchemaClient()
    schema_client.connect()
    try:
        schema_client.create_schema()
    finally:
        schema_client.close()

    source_reference = "hrp60-alpha"
    fullname = "HrpSixty Alpha"
    passport = "HRP60-P-ALPHA"
    address = "1 Alpha Way"

    fragments = [
        _personal("HrpSixty", "Alpha", passport, source_reference),
        _location(fullname, "Springfield", address, source_reference),
        _professional(fullname, "Engineer", source_reference),
        _bank(passport, "HRP60-IBAN-ALPHA", source_reference),
        _net(address, "10.60.0.1", source_reference),
    ]

    mappings = _run_pipeline(fragments)
    assert len(mappings) == 1, "the five fragments must consolidate into exactly one component"
    mapping = mappings[0]
    assert mapping.status == "complete"

    repository = PersonRepository()
    repository.connect()
    employee_id: int | None = None
    try:
        outcome = repository.insert_mapping(mapping)
        assert outcome.inserted is True
        employee_id = outcome.employee_id
        assert employee_id is not None

        with live_connection.cursor() as cursor:
            cursor.execute(
                "SELECT first_name, last_name, passport FROM employees WHERE id = %s",
                (employee_id,),
            )
            employee_row = cursor.fetchone()
            cursor.execute(
                "SELECT full_name, city, address FROM locations WHERE employee_id = %s",
                (employee_id,),
            )
            location_rows = cursor.fetchall()
            cursor.execute(
                "SELECT full_name, job FROM professional_profiles WHERE employee_id = %s",
                (employee_id,),
            )
            professional_rows = cursor.fetchall()
            cursor.execute(
                "SELECT iban, passport FROM bank_accounts WHERE employee_id = %s",
                (employee_id,),
            )
            bank_rows = cursor.fetchall()
            cursor.execute(
                "SELECT ip_v4 FROM network_data WHERE employee_id = %s",
                (employee_id,),
            )
            net_rows = cursor.fetchall()

        assert employee_row == ("HrpSixty", "Alpha", passport)
        assert location_rows == [(fullname, "Springfield", address)]
        assert professional_rows == [(fullname, "Engineer")]
        assert bank_rows == [("HRP60-IBAN-ALPHA", passport)]
        assert net_rows == [("10.60.0.1",)]
    finally:
        if employee_id is not None:
            _cleanup(live_connection, [employee_id])
        repository.close()


def test_two_distinct_people_in_the_same_run_persist_without_cross_contamination(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.storage.person_repository import PersonRepository
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    schema_client = PostgresSchemaClient()
    schema_client.connect()
    try:
        schema_client.create_schema()
    finally:
        schema_client.close()

    fragments = [
        _personal("HrpSixty", "Beta", "HRP60-P-BETA", "hrp60-beta"),
        _location("HrpSixty Beta", "Shelbyville", "2 Beta Way", "hrp60-beta"),
        _personal("HrpSixty", "Gamma", "HRP60-P-GAMMA", "hrp60-gamma"),
        _location("HrpSixty Gamma", "Capital City", "3 Gamma Way", "hrp60-gamma"),
        # Same fullname as Beta's location but different case/whitespace: an
        # ADR-0006 exact edge must NOT match this to Beta (HRP-50 AC-07).
        _professional("hrpsixty beta ", "Analyst", "hrp60-near-miss"),
    ]

    mappings = _run_pipeline(fragments)
    # Beta, Gamma, and the unrelated near-miss professional fragment (its own
    # single-domain component, since it did not correlate with anyone).
    assert len(mappings) == 3

    by_passport = {m.employees[0].fields.get("passport"): m for m in mappings if m.employees}
    beta_mapping = by_passport["HRP60-P-BETA"]
    gamma_mapping = by_passport["HRP60-P-GAMMA"]
    assert beta_mapping.locations[0].fields["city"] == "Shelbyville"
    assert gamma_mapping.locations[0].fields["city"] == "Capital City"
    # The near-miss professional fragment has no personal candidate row, so
    # PersonRepository would skip it outright (no_personal_domain) -- it is
    # never inserted and therefore cannot cross-contaminate either employee.
    near_miss_mapping = next(m for m in mappings if not m.employees)
    assert near_miss_mapping.professional_profiles

    repository = PersonRepository()
    repository.connect()
    employee_ids: list[int] = []
    try:
        beta_outcome = repository.insert_mapping(beta_mapping)
        gamma_outcome = repository.insert_mapping(gamma_mapping)
        assert beta_outcome.inserted is True
        assert gamma_outcome.inserted is True
        assert beta_outcome.employee_id != gamma_outcome.employee_id
        employee_ids = [
            employee_id
            for employee_id in (beta_outcome.employee_id, gamma_outcome.employee_id)
            if employee_id is not None
        ]

        with live_connection.cursor() as cursor:
            cursor.execute(
                "SELECT employee_id, full_name FROM locations WHERE employee_id = ANY(%s)",
                (employee_ids,),
            )
            rows = dict(cursor.fetchall())
        assert rows == {
            beta_outcome.employee_id: "HrpSixty Beta",
            gamma_outcome.employee_id: "HrpSixty Gamma",
        }
    finally:
        _cleanup(live_connection, employee_ids)
        repository.close()


def test_incomplete_component_persists_only_present_domains(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.storage.person_repository import PersonRepository
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    schema_client = PostgresSchemaClient()
    schema_client.connect()
    try:
        schema_client.create_schema()
    finally:
        schema_client.close()

    passport = "HRP60-P-DELTA"
    fragments = [
        _personal("HrpSixty", "Delta", passport, "hrp60-delta-incomplete"),
        _bank(passport, "HRP60-IBAN-DELTA", "hrp60-delta-incomplete"),
    ]

    mappings = _run_pipeline(fragments)
    assert len(mappings) == 1
    mapping = mappings[0]
    assert mapping.status == "incomplete"
    assert mapping.locations == ()
    assert mapping.professional_profiles == ()
    assert mapping.network_data == ()

    repository = PersonRepository()
    repository.connect()
    employee_id: int | None = None
    try:
        outcome = repository.insert_mapping(mapping)
        assert outcome.inserted is True
        employee_id = outcome.employee_id
        assert employee_id is not None

        with live_connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM bank_accounts WHERE employee_id = %s", (employee_id,)
            )
            bank_count = cursor.fetchone()
            cursor.execute("SELECT count(*) FROM locations WHERE employee_id = %s", (employee_id,))
            location_count = cursor.fetchone()
            cursor.execute(
                "SELECT count(*) FROM professional_profiles WHERE employee_id = %s",
                (employee_id,),
            )
            professional_count = cursor.fetchone()
            cursor.execute(
                "SELECT count(*) FROM network_data WHERE employee_id = %s", (employee_id,)
            )
            net_count = cursor.fetchone()

        assert bank_count == (1,)
        assert location_count == (0,)  # no row fabricated for the absent domain
        assert professional_count == (0,)
        assert net_count == (0,)
    finally:
        if employee_id is not None:
            _cleanup(live_connection, [employee_id])
        repository.close()


def test_late_arriving_grouped_fragment_enriches_existing_employee_through_full_pipeline(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.storage.person_repository import PersonRepository
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    schema_client = PostgresSchemaClient()
    schema_client.connect()
    try:
        schema_client.create_schema()
    finally:
        schema_client.close()

    source_reference = "hrp60-epsilon"
    fullname = "HrpSixty Epsilon"
    passport = "HRP60-P-EPSILON"

    # First arrival: only Personal + Location for this source_reference.
    first_mappings = _run_pipeline(
        [
            _personal("HrpSixty", "Epsilon", passport, source_reference),
            _location(fullname, "Ogdenville", "5 Epsilon Way", source_reference),
        ]
    )
    assert len(first_mappings) == 1

    repository = PersonRepository()
    repository.connect()
    employee_id: int | None = None
    try:
        first_outcome = repository.insert_mapping(first_mappings[0])
        assert first_outcome.inserted is True
        employee_id = first_outcome.employee_id
        assert employee_id is not None

        # Later arrival: the same source_reference, replaying the personal and
        # location fragments (unchanged) plus a genuinely new Professional
        # fragment correlated via the same exact fullname -- simulating a
        # later Kafka event about the same already-processed component.
        second_mappings = _run_pipeline(
            [
                _personal("HrpSixty", "Epsilon", passport, source_reference),
                _location(fullname, "Ogdenville", "5 Epsilon Way", source_reference),
                _professional(fullname, "Consultant", source_reference),
            ]
        )
        assert len(second_mappings) == 1
        second_outcome = repository.insert_mapping(second_mappings[0])

        assert second_outcome.inserted is False
        assert second_outcome.skipped_reason is None
        assert second_outcome.employee_id == employee_id
        assert second_outcome.enriched_tables == ("professional_profiles",)

        with live_connection.cursor() as cursor:
            cursor.execute(
                "SELECT full_name, job FROM professional_profiles WHERE employee_id = %s",
                (employee_id,),
            )
            professional_rows = cursor.fetchall()
            cursor.execute("SELECT count(*) FROM locations WHERE employee_id = %s", (employee_id,))
            location_count = cursor.fetchone()

        assert professional_rows == [(fullname, "Consultant")]
        assert location_count == (1,)  # the replayed location fragment was not duplicated
    finally:
        if employee_id is not None:
            _cleanup(live_connection, [employee_id])
        repository.close()
