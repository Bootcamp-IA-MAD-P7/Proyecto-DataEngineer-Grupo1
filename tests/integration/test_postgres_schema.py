from __future__ import annotations

from collections.abc import Iterator

import psycopg
import pytest

EXPECTED_TABLES = {
    "employees",
    "locations",
    "professional_profiles",
    "bank_accounts",
    "network_data",
    "processing_audit",
}


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
        yield connection
    finally:
        connection.close()


def test_create_schema_is_idempotent_against_a_real_database(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    client = PostgresSchemaClient()
    client.connect()
    try:
        client.create_schema()
        client.create_schema()
    finally:
        client.close()

    with live_connection.cursor() as cursor:
        cursor.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = ANY(%s)",
            (list(EXPECTED_TABLES),),
        )
        found_tables = {row[0] for row in cursor.fetchall()}

    assert found_tables == EXPECTED_TABLES


def test_dependent_tables_have_no_unique_constraint_on_correlation_candidates(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    client = PostgresSchemaClient()
    client.connect()
    try:
        client.create_schema()
    finally:
        client.close()

    with live_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT tc.table_name, kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'UNIQUE'
              AND tc.table_schema = 'public'
              AND tc.table_name = ANY(%s)
            """,
            (list(EXPECTED_TABLES),),
        )
        unique_columns = cursor.fetchall()

    assert unique_columns == []


def test_locations_foreign_key_references_employees(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    client = PostgresSchemaClient()
    client.connect()
    try:
        client.create_schema()
    finally:
        client.close()

    with live_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT ccu.table_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_name = 'locations'
              AND tc.constraint_name = 'fk_locations_employees'
            """
        )
        referenced_tables = {row[0] for row in cursor.fetchall()}

    assert referenced_tables == {"employees"}
