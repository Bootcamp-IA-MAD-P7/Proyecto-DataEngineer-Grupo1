"""HRP-83 integration test: the API skeleton actually connects to a real
PostgreSQL container. See tests/unit/test_api_health.py for the mocked
success/failure-path evidence.
"""

from __future__ import annotations

import psycopg
import pytest
from fastapi.testclient import TestClient


def test_health_reports_ok_against_a_real_postgres_container() -> None:
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
        probe = psycopg.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            connect_timeout=2,
        )
        probe.close()
    except psycopg.OperationalError:
        pytest.skip(
            "PostgreSQL is not reachable; "
            "start it with `docker compose -f infra/compose.dev.yml up -d postgres`."
        )

    from hr_pro_platform.api.main import create_app

    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
