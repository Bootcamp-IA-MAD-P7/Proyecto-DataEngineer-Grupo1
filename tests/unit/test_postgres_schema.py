from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# config.py
# ---------------------------------------------------------------------------


def test_config_loads_postgres_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "test_db")
    monkeypatch.setenv("POSTGRES_USER", "test_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_password")

    from importlib import reload

    from hr_pro_platform.storage import config

    reload(config)

    assert config.POSTGRES_HOST == "localhost"
    assert config.POSTGRES_PORT == "5432"
    assert config.POSTGRES_DB == "test_db"
    assert config.POSTGRES_USER == "test_user"
    assert config.POSTGRES_PASSWORD == "test_password"


# ---------------------------------------------------------------------------
# postgres.py — PostgresSchemaClient
# ---------------------------------------------------------------------------


@patch("hr_pro_platform.storage.postgres.psycopg.connect")
def test_connect_runs_select_1(mock_connect: MagicMock) -> None:
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    mock_connection = MagicMock()
    mock_connect.return_value = mock_connection

    client = PostgresSchemaClient()
    client.connect()

    mock_connection.execute.assert_called_once_with("SELECT 1")


@patch("hr_pro_platform.storage.postgres.psycopg.connect")
def test_connect_raises_on_failure(mock_connect: MagicMock) -> None:
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    mock_connect.side_effect = Exception("connection refused")

    client = PostgresSchemaClient()
    with pytest.raises(Exception, match="connection refused"):
        client.connect()


def test_create_schema_executes_every_statement() -> None:
    from hr_pro_platform.storage.postgres import _SCHEMA_STATEMENTS, PostgresSchemaClient

    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_connection = MagicMock()
    mock_connection.cursor.return_value = mock_cursor

    client = PostgresSchemaClient()
    client._connection = mock_connection

    client.create_schema()

    assert mock_cursor.execute.call_count == len(_SCHEMA_STATEMENTS)
    mock_connection.commit.assert_called_once()


def test_create_schema_declares_no_unique_business_constraint() -> None:
    """No column that could encode person identity (passport, fullname,
    address, iban, ...) is ever UNIQUE. The one documented exception is
    HRP-58's technical uniqueness index on processing_audit.raw_event_ref,
    an opaque source-idempotency reference, not a business-identity field
    (see docs/specs/HRP-58-avoid-duplicate-records.md)."""

    from hr_pro_platform.storage.postgres import _SCHEMA_STATEMENTS

    unique_statements = [
        statement for statement in _SCHEMA_STATEMENTS if "UNIQUE" in statement.upper()
    ]
    assert len(unique_statements) == 1
    assert "raw_event_ref" in unique_statements[0]
    assert "processing_audit" in unique_statements[0]


@patch("hr_pro_platform.storage.postgres.psycopg.connect")
def test_close_calls_connection_close(mock_connect: MagicMock) -> None:
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    mock_connection = MagicMock()
    mock_connect.return_value = mock_connection

    client = PostgresSchemaClient()
    client._connection = mock_connection
    client.close()

    mock_connection.close.assert_called_once()


def test_close_noop_when_not_connected() -> None:
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    client = PostgresSchemaClient()
    client.close()
