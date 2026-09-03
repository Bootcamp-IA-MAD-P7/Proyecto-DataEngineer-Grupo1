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
    from hr_pro_platform.storage.person_repository import PersonRepository
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
    try:
        outcome = repository.insert_mapping(mapping)

        assert outcome.inserted is True
        assert outcome.employee_id is not None

        with live_connection.cursor() as cursor:
            cursor.execute(
                "SELECT first_name, passport FROM employees WHERE id = %s",
                (outcome.employee_id,),
            )
            employee_row = cursor.fetchone()
            cursor.execute(
                "SELECT full_name, employee_id FROM locations WHERE employee_id = %s",
                (outcome.employee_id,),
            )
            location_row = cursor.fetchone()

        assert employee_row == ("IntegrationTest", "INTEGRATION-TEST-P-001")
        assert location_row == ("IntegrationTest Fixture", outcome.employee_id)
    finally:
        with live_connection.cursor() as cleanup_cursor:
            cleanup_cursor.execute(
                "DELETE FROM employees WHERE passport = %s", ("INTEGRATION-TEST-P-001",)
            )
        live_connection.commit()
        repository.close()
