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
from hr_pro_platform.api.statistics import (
    EmployeesMissingDomain,
    RowsPerTable,
    compute_statistics,
)

# count_rows_per_table() issues one SELECT count(*) per table, in this
# order, each consumed via cursor.fetchone(). Then
# count_employees_missing_each_domain() issues one further aggregate query,
# also consumed via cursor.fetchone(), returning one row of four counts
# (locations, professional_profiles, bank_accounts, network_data) -- no
# per-employee row is ever fetched.
_FETCHONE_SIDE_EFFECT = [
    (10,),  # employees
    (4,),  # locations
    (3,),  # professional_profiles
    (2,),  # bank_accounts
    (1,),  # network_data
    (7,),  # processing_audit
    (3, 2, 1, 4),  # employees_missing_domain aggregate row
]
_EXPECTED_ROWS_PER_TABLE = RowsPerTable(
    employees=10,
    locations=4,
    professional_profiles=3,
    bank_accounts=2,
    network_data=1,
    processing_audit=7,
)
_EXPECTED_MISSING_DOMAIN = EmployeesMissingDomain(
    locations=3,
    professional_profiles=2,
    bank_accounts=1,
    network_data=4,
)


def _cursor_with_fixture_data() -> MagicMock:
    cursor = MagicMock()
    cursor.fetchone.side_effect = list(_FETCHONE_SIDE_EFFECT)
    return cursor


def _client_with_fake_cursor(cursor: MagicMock) -> TestClient:
    app = create_app()

    def fake_connection() -> Iterator[MagicMock]:
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        yield connection

    app.dependency_overrides[get_connection] = fake_connection
    return TestClient(app)


def test_compute_statistics_uses_only_aggregate_queries() -> None:
    cursor = _cursor_with_fixture_data()

    result = compute_statistics(cursor)

    assert result.rows_per_table == _EXPECTED_ROWS_PER_TABLE
    assert result.employees_missing_domain == _EXPECTED_MISSING_DOMAIN
    # Exactly 7 aggregate queries (6 table counts + 1 missing-domain
    # aggregate), never a per-employee fetchall -- proves no per-employee
    # data is materialized to answer this endpoint.
    assert cursor.fetchone.call_count == 7
    cursor.fetchall.assert_not_called()


def test_get_statistics_returns_the_computed_result() -> None:
    client = _client_with_fake_cursor(_cursor_with_fixture_data())

    response = client.get("/statistics")

    assert response.status_code == 200
    assert response.json() == {
        "rows_per_table": _EXPECTED_ROWS_PER_TABLE.model_dump(),
        "employees_missing_domain": _EXPECTED_MISSING_DOMAIN.model_dump(),
    }


def test_response_models_only_expose_allowed_aggregate_fields() -> None:
    """Structural guarantee (not just a runtime blacklist check on one
    instance): the response models' own schema cannot carry a per-record
    field -- an employee_id, an iban/salary, or any other column value --
    without a visible, reviewable change to these field lists.
    """

    forbidden_fields = {
        "employee_id",
        "iban",
        "salary",
        "passport",
        "city",
        "job",
        "address",
        "full_name",
    }
    assert forbidden_fields.isdisjoint(RowsPerTable.model_fields)
    assert forbidden_fields.isdisjoint(EmployeesMissingDomain.model_fields)
    assert set(RowsPerTable.model_fields) == {
        "employees",
        "locations",
        "professional_profiles",
        "bank_accounts",
        "network_data",
        "processing_audit",
    }
    assert set(EmployeesMissingDomain.model_fields) == {
        "locations",
        "professional_profiles",
        "bank_accounts",
        "network_data",
    }
    # Every field is a plain int -- no field can carry a string/record value.
    assert all(field.annotation is int for field in RowsPerTable.model_fields.values())
    assert all(field.annotation is int for field in EmployeesMissingDomain.model_fields.values())


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
