"""HRP-85 integration test: /people/search/by-location-profession does a
real round-trip against a real PostgreSQL container. See
tests/unit/test_api_people_search_by_location_profession.py for the
mocked-cursor evidence.
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


def test_search_by_location_and_profession_finds_seeded_employees(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.api.main import create_app

    employee_ids: list[int] = []
    with live_connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO employees (first_name, last_name, passport) "
            "VALUES (%s, %s, %s) RETURNING id",
            ("HRP85", "Match", "HRP85-P-MATCH"),
        )
        matching_id = cursor.fetchone()[0]  # type: ignore[index]
        employee_ids.append(matching_id)
        cursor.execute(
            "INSERT INTO locations (employee_id, full_name, city, address) VALUES (%s, %s, %s, %s)",
            (matching_id, "HRP85 Match", "HRP85-City", "HRP85-Address"),
        )
        cursor.execute(
            "INSERT INTO professional_profiles (employee_id, full_name, job) VALUES (%s, %s, %s)",
            (matching_id, "HRP85 Match", "HRP85-Job"),
        )

        cursor.execute(
            "INSERT INTO employees (first_name, last_name, passport) "
            "VALUES (%s, %s, %s) RETURNING id",
            ("HRP85", "Other", "HRP85-P-OTHER"),
        )
        other_id = cursor.fetchone()[0]  # type: ignore[index]
        employee_ids.append(other_id)
        cursor.execute(
            "INSERT INTO locations (employee_id, full_name, city, address) VALUES (%s, %s, %s, %s)",
            (other_id, "HRP85 Other", "HRP85-City", "HRP85-Different-Address"),
        )
        cursor.execute(
            "INSERT INTO professional_profiles (employee_id, full_name, job) VALUES (%s, %s, %s)",
            (other_id, "HRP85 Other", "HRP85-Different-Job"),
        )
    live_connection.commit()

    try:
        client = TestClient(create_app())

        by_city = client.get("/people/search/by-location-profession", params={"city": "HRP85-City"})
        assert by_city.status_code == 200
        assert {row["id"] for row in by_city.json()} == set(employee_ids)

        by_city_and_job = client.get(
            "/people/search/by-location-profession",
            params={"city": "HRP85-City", "job": "HRP85-Job"},
        )
        assert by_city_and_job.status_code == 200
        body = by_city_and_job.json()
        assert [row["id"] for row in body] == [matching_id]
        assert body[0]["locations"] == [
            {
                "full_name": "HRP85 Match",
                "city": "HRP85-City",
                "address": "HRP85-Address",
                "ip_v4": None,
            }
        ]
        assert body[0]["professional_profiles"] == [
            {
                "full_name": "HRP85 Match",
                "company": None,
                "company_address": None,
                "company_email": None,
                "company_telephone_number": None,
                "job": "HRP85-Job",
            }
        ]

        no_match = client.get(
            "/people/search/by-location-profession",
            params={"city": "HRP85-City", "job": "no-such-job"},
        )
        assert no_match.status_code == 200
        assert no_match.json() == []
    finally:
        with live_connection.cursor() as cleanup_cursor:
            for employee_id in employee_ids:
                cleanup_cursor.execute(
                    "DELETE FROM processing_audit WHERE employee_id = %s", (employee_id,)
                )
                cleanup_cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
        live_connection.commit()
