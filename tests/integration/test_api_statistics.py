"""HRP-86 integration test: /statistics does a real round-trip against a
real PostgreSQL container.

The database may already hold unrelated rows (other tests, prior manual
runs), so this test never asserts an absolute count -- only the *delta*
between a baseline snapshot and a snapshot taken after inserting a known
set of synthetic employees with distinguishable missing/present domains.
See tests/unit/test_api_statistics.py for the mocked-cursor evidence.
"""

from __future__ import annotations

from collections.abc import Iterator

import psycopg
import pytest
from fastapi.testclient import TestClient


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
        from hr_pro_platform.storage.postgres import PostgresSchemaClient

        schema_client = PostgresSchemaClient()
        schema_client.connect()
        try:
            schema_client.create_schema()
        finally:
            schema_client.close()
        yield connection
    finally:
        connection.close()


def _delta(after: dict[str, int], before: dict[str, int]) -> dict[str, int]:
    return {key: after[key] - before.get(key, 0) for key in after}


def test_statistics_reflects_inserted_employees_and_missing_domains(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.api.main import create_app

    client = TestClient(create_app())
    baseline = client.get("/statistics").json()
    assert baseline["rows_per_table"].keys() == {
        "employees",
        "locations",
        "professional_profiles",
        "bank_accounts",
        "network_data",
        "processing_audit",
    }
    assert baseline["employees_missing_domain"].keys() == {
        "locations",
        "professional_profiles",
        "bank_accounts",
        "network_data",
    }

    employee_ids: list[int] = []
    with live_connection.cursor() as cursor:
        # Employee A: has a location, missing professional_profiles,
        # bank_accounts and network_data.
        cursor.execute(
            "INSERT INTO employees (first_name, last_name, passport) "
            "VALUES (%s, %s, %s) RETURNING id",
            ("HRP86", "HasLocation", "HRP86-P-A"),
        )
        employee_a = cursor.fetchone()[0]  # type: ignore[index]
        employee_ids.append(employee_a)
        cursor.execute(
            "INSERT INTO locations (employee_id, full_name, city) VALUES (%s, %s, %s)",
            (employee_a, "HRP86 HasLocation", "HRP86-City"),
        )

        # Employee B: has nothing beyond the employees row -- missing all
        # four dependent domains.
        cursor.execute(
            "INSERT INTO employees (first_name, last_name, passport) "
            "VALUES (%s, %s, %s) RETURNING id",
            ("HRP86", "Empty", "HRP86-P-B"),
        )
        employee_b = cursor.fetchone()[0]  # type: ignore[index]
        employee_ids.append(employee_b)
    live_connection.commit()

    try:
        after = client.get("/statistics").json()
        rows_delta = _delta(after["rows_per_table"], baseline["rows_per_table"])
        missing_delta = _delta(
            after["employees_missing_domain"], baseline["employees_missing_domain"]
        )

        assert rows_delta == {
            "employees": 2,
            "locations": 1,
            "professional_profiles": 0,
            "bank_accounts": 0,
            "network_data": 0,
            "processing_audit": 0,
        }
        # Employee A is missing 3 domains (not locations); employee B is
        # missing all 4 -- so "locations" gets +1 (only B) and the other
        # three domains get +2 (both A and B).
        assert missing_delta == {
            "locations": 1,
            "professional_profiles": 2,
            "bank_accounts": 2,
            "network_data": 2,
        }
        # No individual name or column value ever appears in the response
        # (the response schema itself has no employee_id field either --
        # see test_statistics_response_never_includes_individual_record_fields).
        assert "HRP86-P-A" not in str(after)
        assert "HRP86-City" not in str(after)
    finally:
        with live_connection.cursor() as cleanup_cursor:
            for employee_id in employee_ids:
                cleanup_cursor.execute(
                    "DELETE FROM processing_audit WHERE employee_id = %s", (employee_id,)
                )
                cleanup_cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
        live_connection.commit()

        restored = client.get("/statistics").json()
        assert restored == baseline
