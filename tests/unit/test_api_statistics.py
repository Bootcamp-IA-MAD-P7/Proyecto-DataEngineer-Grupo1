"""Unit tests for the HRP-86 /statistics endpoint.

Uses FastAPI's dependency override mechanism to substitute
``get_connection`` with a fake cursor -- no real database is required.
See tests/integration/test_api_statistics.py for the real-database
evidence (delta assertions against a real PostgreSQL container).
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from unittest.mock import MagicMock

import psycopg
import pytest
from fastapi.testclient import TestClient

from hr_pro_platform.api.db import get_connection
from hr_pro_platform.api.main import create_app
from hr_pro_platform.api.statistics import compute_statistics

# count_rows_per_table() issues one SELECT count(*) per table, in this order,
# each consumed via cursor.fetchone().
_ROWS_PER_TABLE_FETCHONE_SIDE_EFFECT = [(10,), (4,), (3,), (2,), (1,), (7,)]
_EXPECTED_ROWS_PER_TABLE = {
    "employees": 10,
    "locations": 4,
    "professional_profiles": 3,
    "bank_accounts": 2,
    "network_data": 1,
    "processing_audit": 7,
}
# find_incomplete_employees() issues one query returning
# (employee_id, locations_count, professional_profiles_count,
#  bank_accounts_count, network_data_count) per employee.
_INCOMPLETE_EMPLOYEES_FETCHALL_RETURN = [
    (1, 0, 1, 1, 1),  # employee 1: missing only locations
    (2, 1, 0, 0, 1),  # employee 2: missing professional_profiles and bank_accounts
]
_EXPECTED_MISSING_DOMAIN = {
    "locations": 1,
    "professional_profiles": 1,
    "bank_accounts": 1,
    "network_data": 0,
}


def _cursor_with_fixture_data() -> MagicMock:
    cursor = MagicMock()
    cursor.fetchone.side_effect = _ROWS_PER_TABLE_FETCHONE_SIDE_EFFECT
    cursor.fetchall.return_value = _INCOMPLETE_EMPLOYEES_FETCHALL_RETURN
    return cursor


def _client_with_fake_cursor(cursor: MagicMock) -> TestClient:
    app = create_app()

    def fake_connection() -> Iterator[MagicMock]:
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        yield connection

    app.dependency_overrides[get_connection] = fake_connection
    return TestClient(app)


def test_compute_statistics_aggregates_counts_and_missing_domains() -> None:
    cursor = _cursor_with_fixture_data()

    result = compute_statistics(cursor)

    assert result.rows_per_table == _EXPECTED_ROWS_PER_TABLE
    assert result.employees_missing_domain == _EXPECTED_MISSING_DOMAIN


def test_get_statistics_returns_the_computed_result() -> None:
    client = _client_with_fake_cursor(_cursor_with_fixture_data())

    response = client.get("/statistics")

    assert response.status_code == 200
    assert response.json() == {
        "rows_per_table": _EXPECTED_ROWS_PER_TABLE,
        "employees_missing_domain": _EXPECTED_MISSING_DOMAIN,
    }


def test_statistics_response_never_includes_individual_record_fields() -> None:
    client = _client_with_fake_cursor(_cursor_with_fixture_data())

    body = client.get("/statistics").json()

    # Only the two aggregate top-level keys, never a per-record field name
    # (employee_id, iban, salary, city, job, ...) leaking into the response.
    assert set(body) == {"rows_per_table", "employees_missing_domain"}
    forbidden_fields = {"employee_id", "iban", "salary", "passport", "city", "job", "address"}
    assert forbidden_fields.isdisjoint(body["rows_per_table"])
    assert forbidden_fields.isdisjoint(body["employees_missing_domain"])


def test_statistics_reuses_the_shared_database_error_handler(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = create_app()

    def failing_connection() -> Iterator[MagicMock]:
        raise psycopg.OperationalError("connection to server failed: sensitive-detail-marker")
        yield  # pragma: no cover -- unreachable, keeps this a generator

    app.dependency_overrides[get_connection] = failing_connection
    client = TestClient(app, raise_server_exceptions=False)

    with caplog.at_level(logging.ERROR, logger="api"):
        response = client.get("/statistics")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "sensitive-detail-marker" not in response.text
    assert "sensitive-detail-marker" not in caplog.text


def test_existing_routes_are_unaffected() -> None:
    """HRP-86 must not change HRP-84/85's existing routes or response shapes."""
    cursor = MagicMock()
    cursor.fetchall.side_effect = [
        [(1, "Ana", "Gomez", ["F"], "600000000", "ana@example.test", "P-1")],
        [],
        [],
    ]
    client = _client_with_fake_cursor(cursor)

    response = client.get("/people/search", params={"passport": "P-1"})

    assert response.status_code == 200
    assert response.json()[0]["id"] == 1
