"""HRP-59 integration tests: read-only SQL validation queries.

Every check in storage/validation_queries.py is exercised here against a
real PostgreSQL container with minimal synthetic data inserted by each
test itself -- never assumed to pre-exist. See
docs/specs/HRP-59-sql-validation-queries.md for what each check proves and
does not prove.
"""

from __future__ import annotations

from collections.abc import Iterator

import psycopg
import pytest


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


def _insert_employee(connection: psycopg.Connection[tuple[object, ...]], passport: str) -> int:
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO employees (first_name, last_name, passport) "
            "VALUES (%s, %s, %s) RETURNING id",
            ("HRP59", "Fixture", passport),
        )
        result = cursor.fetchone()
        assert result is not None
    connection.commit()
    return int(result[0])


def _cleanup_employees(
    connection: psycopg.Connection[tuple[object, ...]], employee_ids: list[int]
) -> None:
    with connection.cursor() as cursor:
        for employee_id in employee_ids:
            cursor.execute("DELETE FROM processing_audit WHERE employee_id = %s", (employee_id,))
            cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
    connection.commit()


def test_foreign_key_constraints_are_present_on_every_dependent_table(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.storage.validation_queries import (
        DEPENDENT_TABLES,
        check_foreign_key_constraints_present,
    )

    with live_connection.cursor() as cursor:
        result = check_foreign_key_constraints_present(cursor)

    assert result == {table: True for table in DEPENDENT_TABLES}


def test_no_dependent_rows_are_orphaned_after_a_normal_insert(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.storage.validation_queries import (
        DEPENDENT_TABLES,
        find_orphaned_dependent_rows,
    )

    employee_id = _insert_employee(live_connection, "HRP59-P-ORPHAN-CHECK")
    try:
        with live_connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO locations (employee_id, full_name, city, address) "
                "VALUES (%s, %s, %s, %s)",
                (employee_id, "HRP59 Fixture", "Springfield", "1 Fixture Way"),
            )
        live_connection.commit()

        with live_connection.cursor() as cursor:
            orphans = find_orphaned_dependent_rows(cursor)

        assert orphans == {table: () for table in DEPENDENT_TABLES}
    finally:
        _cleanup_employees(live_connection, [employee_id])


def test_incomplete_employee_reports_its_missing_domains(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.storage.validation_queries import find_incomplete_employees

    employee_id = _insert_employee(live_connection, "HRP59-P-INCOMPLETE")
    try:
        with live_connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO bank_accounts (employee_id, iban, passport, salary) "
                "VALUES (%s, %s, %s, %s)",
                (employee_id, "HRP59-IBAN-INCOMPLETE", "HRP59-P-INCOMPLETE", "50000"),
            )
        live_connection.commit()

        with live_connection.cursor() as cursor:
            incomplete = find_incomplete_employees(cursor)

        assert employee_id in incomplete
        assert set(incomplete[employee_id]) == {
            "locations",
            "professional_profiles",
            "network_data",
        }
    finally:
        _cleanup_employees(live_connection, [employee_id])


def test_exact_duplicate_dependent_row_is_detected(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.storage.validation_queries import find_exact_duplicate_dependent_rows

    employee_id = _insert_employee(live_connection, "HRP59-P-DUPLICATE")
    try:
        with live_connection.cursor() as cursor:
            for _ in range(2):
                # Inserted directly, bypassing PersonRepository's own
                # exact-match check (HRP-57), to simulate a defect this
                # check exists to catch -- not to prove HRP-57 is broken.
                cursor.execute(
                    "INSERT INTO locations (employee_id, full_name, city, address) "
                    "VALUES (%s, %s, %s, %s)",
                    (employee_id, "HRP59 Fixture", "Shelbyville", "2 Fixture Way"),
                )
        live_connection.commit()

        with live_connection.cursor() as cursor:
            duplicates = find_exact_duplicate_dependent_rows(cursor)

        assert duplicates["locations"] == (
            (employee_id, "HRP59 Fixture", "Shelbyville", "2 Fixture Way", None),
        )
        assert duplicates["professional_profiles"] == ()
        assert duplicates["bank_accounts"] == ()
        assert duplicates["network_data"] == ()
    finally:
        _cleanup_employees(live_connection, [employee_id])


def test_duplicate_processing_audit_reference_is_rejected_by_the_unique_index(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.storage.validation_queries import (
        find_duplicate_processing_audit_references,
    )

    employee_id = _insert_employee(live_connection, "HRP59-P-AUDIT-DUP")
    try:
        with live_connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO processing_audit (employee_id, stage, status, raw_event_ref) "
                "VALUES (%s, %s, %s, %s)",
                (employee_id, "insert", "inserted", "hrp59-audit-dup-source"),
            )
        live_connection.commit()

        # HRP-58's unique index on raw_event_ref must reject a second row
        # with the same reference -- this proves the index still exists
        # and is enforced, which is exactly what this check's clean result
        # would otherwise only imply indirectly.
        with pytest.raises(psycopg.errors.UniqueViolation):
            with live_connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO processing_audit (employee_id, stage, status, raw_event_ref) "
                    "VALUES (%s, %s, %s, %s)",
                    (employee_id, "insert", "inserted", "hrp59-audit-dup-source"),
                )
        live_connection.rollback()

        with live_connection.cursor() as cursor:
            duplicates = find_duplicate_processing_audit_references(cursor)

        assert "hrp59-audit-dup-source" not in duplicates
    finally:
        _cleanup_employees(live_connection, [employee_id])


def test_row_counts_reflect_inserted_synthetic_data(
    live_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.storage.validation_queries import count_rows_per_table

    with live_connection.cursor() as cursor:
        before = count_rows_per_table(cursor)

    employee_id = _insert_employee(live_connection, "HRP59-P-COUNT")
    try:
        with live_connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO network_data (employee_id, ip_v4) VALUES (%s, %s)",
                (employee_id, "10.59.0.1"),
            )
        live_connection.commit()

        with live_connection.cursor() as cursor:
            after = count_rows_per_table(cursor)

        assert after["employees"] == before["employees"] + 1
        assert after["network_data"] == before["network_data"] + 1
        assert after["locations"] == before["locations"]
        assert after["professional_profiles"] == before["professional_profiles"]
        assert after["bank_accounts"] == before["bank_accounts"]
    finally:
        _cleanup_employees(live_connection, [employee_id])
