"""HRP-84 integration test: /people/search does a real round-trip
against a real PostgreSQL container. See
tests/unit/test_api_people_search.py for the mocked-cursor evidence.
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


def test_search_finds_a_seeded_employee_with_its_dependent_rows(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.api.main import create_app

    with live_connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO employees (first_name, last_name, passport) "
            "VALUES (%s, %s, %s) RETURNING id",
            ("HRP84", "Fixture", "HRP84-P-INTEGRATION"),
        )
        employee_id = cursor.fetchone()[0]  # type: ignore[index]
        cursor.execute(
            "INSERT INTO locations (employee_id, full_name, city, address) VALUES (%s, %s, %s, %s)",
            (employee_id, "HRP84 Fixture", "Shelbyville", "2 Fixture Way"),
        )
    live_connection.commit()

    try:
        client = TestClient(create_app())

        response = client.get("/people/search", params={"passport": "HRP84-P-INTEGRATION"})

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["id"] == employee_id
        assert body[0]["passport"] == "HRP84-P-INTEGRATION"
        assert body[0]["locations"] == [
            {
                "full_name": "HRP84 Fixture",
                "city": "Shelbyville",
                "address": "2 Fixture Way",
                "ip_v4": None,
            }
        ]
        assert body[0]["professional_profiles"] == []

        not_found = client.get("/people/search", params={"passport": "no-such-passport-hrp84"})
        assert not_found.status_code == 200
        assert not_found.json() == []
    finally:
        with live_connection.cursor() as cleanup_cursor:
            cleanup_cursor.execute(
                "DELETE FROM processing_audit WHERE employee_id = %s", (employee_id,)
            )
            cleanup_cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
        live_connection.commit()
