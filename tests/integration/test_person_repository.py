"""HRP-56 integration test: real insert against the HRP-53 PostgreSQL container.

Reuses the `live_connection` skip pattern from `test_postgres_schema.py`: this
test is skipped automatically whenever PostgreSQL is not reachable, matching
CI's current lack of a live Docker service.
"""

from __future__ import annotations

from collections.abc import Iterator

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


def test_insert_mapping_round_trips_through_a_real_database(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.storage.person_mapper import CandidateRow, PersonRecordMapping
    from hr_pro_platform.storage.person_repository import InsertOutcome, PersonRepository
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    schema_client = PostgresSchemaClient()
    schema_client.connect()
    try:
        schema_client.create_schema()
    finally:
        schema_client.close()

    mapping = PersonRecordMapping(
        status="complete",
        correlation_rules=("personal_bank_passport",),
        provenance=("integration-test-source",),
        employees=(
            CandidateRow(
                table="employees",
                group_key="INTEGRATION-TEST-P-001",
                fields={
                    "first_name": "IntegrationTest",
                    "last_name": "Fixture",
                    "sex": ["X"],
                    "passport": "INTEGRATION-TEST-P-001",
                },
                source_reference="integration-test-source",
            ),
        ),
        locations=(
            CandidateRow(
                table="locations",
                group_key="IntegrationTest Fixture",
                fields={"full_name": "IntegrationTest Fixture", "city": "Springfield"},
                source_reference="integration-test-source",
            ),
        ),
        professional_profiles=(),
        bank_accounts=(),
        network_data=(),
    )

    repository = PersonRepository()
    repository.connect()
    outcome: InsertOutcome | None = None
    try:
        outcome = repository.insert_mapping(mapping)

        assert outcome.inserted is True
        assert outcome.employee_id is not None

        with live_connection.cursor() as cursor:
            cursor.execute(
                "SELECT first_name, passport, sex FROM employees WHERE id = %s",
                (outcome.employee_id,),
            )
            employee_row = cursor.fetchone()
            cursor.execute(
                "SELECT full_name, employee_id FROM locations WHERE employee_id = %s",
                (outcome.employee_id,),
            )
            location_row = cursor.fetchone()

        assert employee_row == ("IntegrationTest", "INTEGRATION-TEST-P-001", ["X"])
        assert location_row == ("IntegrationTest Fixture", outcome.employee_id)
    finally:
        try:
            if outcome is not None and outcome.employee_id is not None:
                # Scoped to exactly the employee row this test created, not a
                # fixed predicate that could match unrelated data.
                with live_connection.cursor() as cleanup_cursor:
                    cleanup_cursor.execute(
                        "DELETE FROM employees WHERE id = %s", (outcome.employee_id,)
                    )
                    cleanup_cursor.execute(
                        "DELETE FROM processing_audit WHERE raw_event_ref = %s",
                        (mapping.employees[0].source_reference,),
                    )
                live_connection.commit()
        finally:
            repository.close()


def test_reprocessing_the_same_source_reference_inserts_once_and_skips_the_second_time(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.storage.person_mapper import CandidateRow, PersonRecordMapping
    from hr_pro_platform.storage.person_repository import InsertOutcome, PersonRepository
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    schema_client = PostgresSchemaClient()
    schema_client.connect()
    try:
        schema_client.create_schema()
    finally:
        schema_client.close()

    mapping = PersonRecordMapping(
        status="complete",
        correlation_rules=(),
        provenance=("integration-test-dedup-source",),
        employees=(
            CandidateRow(
                table="employees",
                group_key="INTEGRATION-TEST-P-DEDUP",
                fields={
                    "first_name": "DedupTest",
                    "last_name": "Fixture",
                    "passport": "INTEGRATION-TEST-P-DEDUP",
                },
                source_reference="integration-test-dedup-source",
            ),
        ),
        locations=(),
        professional_profiles=(),
        bank_accounts=(),
        network_data=(),
    )

    repository = PersonRepository()
    repository.connect()
    first_outcome: InsertOutcome | None = None
    second_outcome: InsertOutcome | None = None
    try:
        first_outcome = repository.insert_mapping(mapping)
        second_outcome = repository.insert_mapping(mapping)

        assert first_outcome.inserted is True
        assert second_outcome.inserted is False
        assert second_outcome.skipped_reason == "already_processed"
        assert second_outcome.employee_id is None

        with live_connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM employees WHERE passport = %s",
                ("INTEGRATION-TEST-P-DEDUP",),
            )
            employee_count = cursor.fetchone()
            cursor.execute(
                "SELECT count(*) FROM processing_audit WHERE raw_event_ref = %s",
                ("integration-test-dedup-source",),
            )
            audit_count = cursor.fetchone()

        assert employee_count == (1,)  # not duplicated by the second attempt
        assert audit_count == (1,)  # not duplicated either
    finally:
        try:
            if first_outcome is not None and first_outcome.employee_id is not None:
                with live_connection.cursor() as cleanup_cursor:
                    cleanup_cursor.execute(
                        "DELETE FROM employees WHERE id = %s", (first_outcome.employee_id,)
                    )
                    cleanup_cursor.execute(
                        "DELETE FROM processing_audit WHERE raw_event_ref = %s",
                        ("integration-test-dedup-source",),
                    )
                live_connection.commit()
        finally:
            repository.close()


def test_two_distinct_source_references_both_insert_and_only_the_replay_skips(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    """Real-database proof that the idempotency check filters by the exact
    requested source_reference, not by "any row exists". A mock cannot prove
    this -- it only simulates application logic, not actual SQL filtering
    (see the equivalent, mock-only test in tests/unit/test_person_repository.py
    for why this scenario needs a live database to be meaningful).
    """
    from hr_pro_platform.storage.person_mapper import CandidateRow, PersonRecordMapping
    from hr_pro_platform.storage.person_repository import InsertOutcome, PersonRepository
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    schema_client = PostgresSchemaClient()
    schema_client.connect()
    try:
        schema_client.create_schema()
    finally:
        schema_client.close()

    def build_mapping(passport: str, source_reference: str) -> PersonRecordMapping:
        # Deliberately identical business fields across A and B; only
        # source_reference differs, so a lookup that ignores the requested
        # reference (e.g. "SELECT 1 FROM processing_audit LIMIT 1") would
        # incorrectly report B as already processed once A is inserted.
        return PersonRecordMapping(
            status="complete",
            correlation_rules=(),
            provenance=(source_reference,),
            employees=(
                CandidateRow(
                    table="employees",
                    group_key=passport,
                    fields={
                        "first_name": "TwoRefTest",
                        "last_name": "Fixture",
                        "passport": passport,
                    },
                    source_reference=source_reference,
                ),
            ),
            locations=(),
            professional_profiles=(),
            bank_accounts=(),
            network_data=(),
        )

    mapping_a = build_mapping("INTEGRATION-TEST-P-REF-A", "integration-test-source-A")
    mapping_b = build_mapping("INTEGRATION-TEST-P-REF-B", "integration-test-source-B")

    repository = PersonRepository()
    repository.connect()
    outcome_a: InsertOutcome | None = None
    outcome_b: InsertOutcome | None = None
    try:
        outcome_a = repository.insert_mapping(mapping_a)
        outcome_b = repository.insert_mapping(mapping_b)
        replay_a = repository.insert_mapping(mapping_a)
        replay_b = repository.insert_mapping(mapping_b)

        assert outcome_a.inserted is True
        assert outcome_b.inserted is True
        assert replay_a.inserted is False
        assert replay_a.skipped_reason == "already_processed"
        assert replay_b.inserted is False
        assert replay_b.skipped_reason == "already_processed"

        with live_connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM employees WHERE passport IN (%s, %s)",
                ("INTEGRATION-TEST-P-REF-A", "INTEGRATION-TEST-P-REF-B"),
            )
            employee_count = cursor.fetchone()

        assert employee_count == (2,)  # one per reference, no cross-reference skip
    finally:
        try:
            with live_connection.cursor() as cleanup_cursor:
                for outcome in (outcome_a, outcome_b):
                    if outcome is not None and outcome.employee_id is not None:
                        cleanup_cursor.execute(
                            "DELETE FROM employees WHERE id = %s", (outcome.employee_id,)
                        )
                cleanup_cursor.execute(
                    "DELETE FROM processing_audit WHERE raw_event_ref = ANY(%s)",
                    (["integration-test-source-A", "integration-test-source-B"],),
                )
            live_connection.commit()
        finally:
            repository.close()
