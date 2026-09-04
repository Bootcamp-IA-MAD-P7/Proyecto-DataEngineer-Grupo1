"""Unit tests for the HRP-83 API skeleton's /health endpoint.

Uses FastAPI's dependency override mechanism to substitute
``get_connection`` -- no real database is required for these tests.
See tests/integration/test_api_health.py for the real-database
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


def test_health_returns_ok_when_the_database_dependency_succeeds() -> None:
    app = create_app()

    def fake_connection() -> Iterator[MagicMock]:
        connection = MagicMock()
        yield connection

    app.dependency_overrides[get_connection] = fake_connection
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_returns_a_safe_unavailable_response_when_the_database_is_down(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = create_app()

    def failing_connection() -> Iterator[MagicMock]:
        # Real psycopg errors carry a message/DETAIL that can echo rejected
        # values (per docs/backend-standards.md); a sensitive marker here
        # proves the response body and log line never leak it.
        raise psycopg.OperationalError("connection to server failed: sensitive-detail-marker")
        yield  # pragma: no cover -- unreachable, keeps this a generator

    app.dependency_overrides[get_connection] = failing_connection
    client = TestClient(app, raise_server_exceptions=False)

    with caplog.at_level(logging.ERROR, logger="api"):
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "sensitive-detail-marker" not in response.text
    assert "sensitive-detail-marker" not in caplog.text
    assert "OperationalError" in caplog.text


def test_health_returns_a_safe_unavailable_response_when_the_query_itself_fails(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A connection that opens successfully but fails on the query itself
    (e.g. the server drops mid-request) must be handled the same way as a
    connection that never opened."""

    app = create_app()

    def connection_that_fails_on_query() -> Iterator[MagicMock]:
        connection = MagicMock()
        connection.execute.side_effect = psycopg.OperationalError(
            "server closed the connection unexpectedly: sensitive-detail-marker"
        )
        yield connection

    app.dependency_overrides[get_connection] = connection_that_fails_on_query
    client = TestClient(app, raise_server_exceptions=False)

    with caplog.at_level(logging.ERROR, logger="api"):
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "sensitive-detail-marker" not in response.text
    assert "sensitive-detail-marker" not in caplog.text
