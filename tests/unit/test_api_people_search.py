"""Unit tests for the HRP-84 /people/search endpoint.

Uses FastAPI's dependency override mechanism to substitute
``get_connection`` with a fake cursor -- no real database is required.
See tests/integration/test_api_people_search.py for the real-database
evidence.
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


def _client_with_fake_cursor(cursor: MagicMock) -> TestClient:
    app = create_app()

    def fake_connection() -> Iterator[MagicMock]:
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        yield connection

    app.dependency_overrides[get_connection] = fake_connection
    return TestClient(app)


def test_search_returns_a_match_with_its_dependent_rows() -> None:
    cursor = MagicMock()
    cursor.fetchall.side_effect = [
        [(1, "Ana", "Gomez", ["F"], "600000000", "ana@example.test", "P-1")],  # employees
        [("Ana Gomez", "Springfield", "1 Fixture Way", None)],  # locations
        [("Ana Gomez", "Acme", "1 Acme Rd", "hr@acme.test", "600111000", "Engineer")],
    ]
    client = _client_with_fake_cursor(cursor)

    response = client.get("/people/search", params={"passport": "P-1"})

    assert response.status_code == 200
    body = response.json()
    assert body == [
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
    # bank_accounts is never queried -- excluded per the spec's open decision.
    executed_sql = " ".join(call.args[0].as_string(None) for call in cursor.execute.call_args_list)
    assert "bank_accounts" not in executed_sql


def test_search_returns_an_empty_list_when_nothing_matches() -> None:
    cursor = MagicMock()
    cursor.fetchall.return_value = []
    client = _client_with_fake_cursor(cursor)

    response = client.get("/people/search", params={"passport": "no-such-passport"})

    assert response.status_code == 200
    assert response.json() == []


def test_search_rejects_a_request_with_no_filter() -> None:
    cursor = MagicMock()
    client = _client_with_fake_cursor(cursor)

    response = client.get("/people/search")

    assert response.status_code == 400
    cursor.execute.assert_not_called()


@pytest.mark.parametrize(
    "params", [{"passport": "P-1", "limit": 0}, {"passport": "P-1", "limit": 101}]
)
def test_search_rejects_an_out_of_range_limit(params: dict[str, object]) -> None:
    cursor = MagicMock()
    client = _client_with_fake_cursor(cursor)

    response = client.get("/people/search", params=params)

    assert response.status_code == 400
    cursor.execute.assert_not_called()


def test_search_rejects_a_negative_offset() -> None:
    cursor = MagicMock()
    client = _client_with_fake_cursor(cursor)

    response = client.get("/people/search", params={"passport": "P-1", "offset": -1})

    assert response.status_code == 400
    cursor.execute.assert_not_called()


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
        response = client.get("/people/search", params={"passport": "P-1"})

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "sensitive-detail-marker" not in response.text
    assert "sensitive-detail-marker" not in caplog.text
