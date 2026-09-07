"""Unit tests for the HRP-85 /people/search/by-location-profession endpoint.

Uses FastAPI's dependency override mechanism to substitute
``get_connection`` with a fake cursor -- no real database is required.
See tests/integration/test_api_people_search_by_location_profession.py
for the real-database evidence.
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

ROUTE = "/people/search/by-location-profession"

_EMPLOYEE_ROW = (1, "Ana", "Gomez", ["F"], "600000000", "ana@example.test", "P-1")
_LOCATION_ROW = ("Ana Gomez", "Springfield", "1 Fixture Way", None)
_PROFESSIONAL_ROW = ("Ana Gomez", "Acme", "1 Acme Rd", "hr@acme.test", "600111000", "Engineer")
_EXPECTED_BODY = [
    {
        "id": 1,
        "first_name": "Ana",
        "last_name": "Gomez",
        "sex": ["F"],
        "telephone_number": "600000000",
        "email": "ana@example.test",
        "passport": "P-1",
        "locations": [
            {
                "full_name": "Ana Gomez",
                "city": "Springfield",
                "address": "1 Fixture Way",
                "ip_v4": None,
            }
        ],
        "professional_profiles": [
            {
                "full_name": "Ana Gomez",
                "company": "Acme",
                "company_address": "1 Acme Rd",
                "company_email": "hr@acme.test",
                "company_telephone_number": "600111000",
                "job": "Engineer",
            }
        ],
    }
]


def _client_with_fake_cursor(cursor: MagicMock) -> TestClient:
    app = create_app()

    def fake_connection() -> Iterator[MagicMock]:
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        yield connection

    app.dependency_overrides[get_connection] = fake_connection
    return TestClient(app)


@pytest.mark.parametrize("params", [{"city": "Springfield"}, {"address": "1 Fixture Way"}])
def test_search_by_location_finds_a_match(params: dict[str, str]) -> None:
    cursor = MagicMock()
    cursor.fetchall.side_effect = [
        [(1,)],  # locations: matching employee_id(s)
        [_EMPLOYEE_ROW],  # employees
        [_LOCATION_ROW],  # locations (dependent)
        [_PROFESSIONAL_ROW],  # professional_profiles (dependent)
    ]
    client = _client_with_fake_cursor(cursor)

    response = client.get(ROUTE, params=params)

    assert response.status_code == 200
    assert response.json() == _EXPECTED_BODY


@pytest.mark.parametrize("params", [{"job": "Engineer"}, {"company": "Acme"}])
def test_search_by_profession_finds_a_match(params: dict[str, str]) -> None:
    cursor = MagicMock()
    cursor.fetchall.side_effect = [
        [(1,)],  # professional_profiles: matching employee_id(s)
        [_EMPLOYEE_ROW],  # employees
        [_LOCATION_ROW],  # locations (dependent)
        [_PROFESSIONAL_ROW],  # professional_profiles (dependent)
    ]
    client = _client_with_fake_cursor(cursor)

    response = client.get(ROUTE, params=params)

    assert response.status_code == 200
    assert response.json() == _EXPECTED_BODY


def test_combined_location_and_profession_filters_apply_and_when_both_match() -> None:
    cursor = MagicMock()
    cursor.fetchall.side_effect = [
        [(1,), (2,)],  # locations: employees 1 and 2 match the city
        [(1,)],  # professional_profiles: only employee 1 also matches the job
        [_EMPLOYEE_ROW],  # employees (only id=1 survives the AND)
        [_LOCATION_ROW],
        [_PROFESSIONAL_ROW],
    ]
    client = _client_with_fake_cursor(cursor)

    response = client.get(ROUTE, params={"city": "Springfield", "job": "Engineer"})

    assert response.status_code == 200
    assert response.json() == _EXPECTED_BODY
    # The employees query must only ever ask for the intersected id, never
    # for every employee_id either filter matched on its own -- proves the
    # AND semantics, not an OR that would return employee 2 too.
    employees_call = cursor.execute.call_args_list[2]
    assert employees_call.args[1] == [[1], 20, 0]


def test_combined_location_and_profession_filters_return_empty_when_only_one_matches() -> None:
    cursor = MagicMock()
    cursor.fetchall.side_effect = [
        [(1,)],  # locations: employee 1 matches the city
        [(2,)],  # professional_profiles: employee 2 matches the job (disjoint)
    ]
    client = _client_with_fake_cursor(cursor)

    response = client.get(ROUTE, params={"city": "Springfield", "job": "Engineer"})

    assert response.status_code == 200
    assert response.json() == []
    # An empty intersection must short-circuit: no employees/dependent query.
    assert cursor.execute.call_count == 2


def test_search_returns_an_empty_list_when_nothing_matches() -> None:
    cursor = MagicMock()
    cursor.fetchall.return_value = []
    client = _client_with_fake_cursor(cursor)

    response = client.get(ROUTE, params={"city": "no-such-city"})

    assert response.status_code == 200
    assert response.json() == []


def test_search_rejects_a_request_with_no_filter() -> None:
    cursor = MagicMock()
    client = _client_with_fake_cursor(cursor)

    response = client.get(ROUTE)

    assert response.status_code == 400
    cursor.execute.assert_not_called()


@pytest.mark.parametrize(
    "params", [{"city": "Springfield", "limit": 0}, {"city": "Springfield", "limit": 101}]
)
def test_search_rejects_an_out_of_range_limit(params: dict[str, object]) -> None:
    cursor = MagicMock()
    client = _client_with_fake_cursor(cursor)

    response = client.get(ROUTE, params=params)

    assert response.status_code == 400
    cursor.execute.assert_not_called()


def test_search_rejects_a_negative_offset() -> None:
    cursor = MagicMock()
    client = _client_with_fake_cursor(cursor)

    response = client.get(ROUTE, params={"city": "Springfield", "offset": -1})

    assert response.status_code == 400
    cursor.execute.assert_not_called()


def test_search_never_queries_bank_accounts() -> None:
    cursor = MagicMock()
    cursor.fetchall.side_effect = [
        [(1,)],
        [_EMPLOYEE_ROW],
        [_LOCATION_ROW],
        [_PROFESSIONAL_ROW],
    ]
    client = _client_with_fake_cursor(cursor)

    client.get(ROUTE, params={"city": "Springfield"})

    executed_sql = " ".join(call.args[0].as_string(None) for call in cursor.execute.call_args_list)
    assert "bank_accounts" not in executed_sql


def test_search_reuses_the_shared_database_error_handler(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = create_app()

    def failing_connection() -> Iterator[MagicMock]:
        raise psycopg.OperationalError("connection to server failed: sensitive-detail-marker")
        yield  # pragma: no cover -- unreachable, keeps this a generator

    app.dependency_overrides[get_connection] = failing_connection
    client = TestClient(app, raise_server_exceptions=False)

    with caplog.at_level(logging.ERROR, logger="api"):
        response = client.get(ROUTE, params={"city": "Springfield"})

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "sensitive-detail-marker" not in response.text
    assert "sensitive-detail-marker" not in caplog.text


def test_existing_people_search_endpoint_is_unaffected() -> None:
    """HRP-85 must not change HRP-84's existing route or response shape."""
    cursor = MagicMock()
    cursor.fetchall.side_effect = [
        [_EMPLOYEE_ROW],
        [_LOCATION_ROW],
        [_PROFESSIONAL_ROW],
    ]
    client = _client_with_fake_cursor(cursor)

    response = client.get("/people/search", params={"passport": "P-1"})

    assert response.status_code == 200
    assert response.json() == _EXPECTED_BODY
