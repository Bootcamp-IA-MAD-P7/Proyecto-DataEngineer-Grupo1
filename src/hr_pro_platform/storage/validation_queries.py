"""Read-only SQL validation queries for curated PostgreSQL data.

See docs/specs/HRP-59-sql-validation-queries.md. Every function here only
reads; none inserts, updates or deletes. Each check documents what a clean
result proves and what it does not -- in particular, no check here asserts
real-world person identity or a correlation key beyond what
docs/adr/0006-person-correlation-key.md ("Accepted in principle") approves.

This module defines its own column tuples for exact-duplicate detection
rather than importing person_repository.py's private
``_DEPENDENT_TABLE_COLUMNS``, to avoid coupling a read-only validation
module to a private implementation detail of the write path. Both are kept
in sync by the schema they each describe (HRP-54's ``_SCHEMA_STATEMENTS``),
not by direct code sharing.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import psycopg
from psycopg import sql

DEPENDENT_TABLES: tuple[str, ...] = (
    "locations",
    "professional_profiles",
    "bank_accounts",
    "network_data",
)

# Every non-id, non-employee_id column each dependent table declares in
# storage/postgres.py's _SCHEMA_STATEMENTS (HRP-54).
_DEPENDENT_TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "locations": ("full_name", "city", "address", "ip_v4"),
    "professional_profiles": (
        "full_name",
        "company",
        "company_address",
        "company_email",
        "company_telephone_number",
        "job",
    ),
    "bank_accounts": ("iban", "passport", "salary"),
    "network_data": ("ip_v4",),
}


def check_foreign_key_constraints_present(
    cursor: psycopg.Cursor[Any], tables: Sequence[str] = DEPENDENT_TABLES
) -> dict[str, bool]:
    """Confirm each of ``tables`` (default: the four dependent tables)
    declares a single-column FOREIGN KEY on ``employee_id`` referencing
    ``employees.id``.

    Uses ``pg_catalog.pg_constraint`` (keyed by real OIDs: ``conrelid`` for
    the constrained table, ``confrelid`` for the referenced one) rather
    than the ``information_schema`` constraint-metadata views. Those views
    are keyed by ``constraint_catalog``/``constraint_schema``/
    ``constraint_name`` alone, and constraint *names* are only required to
    be unique per table in PostgreSQL -- two different tables in the same
    schema can legitimately share a constraint name (verified empirically
    against a live database). An earlier version of this function joined
    ``information_schema.table_constraints``/``key_column_usage``/
    ``constraint_column_usage`` on name and schema alone, which let a
    same-named constraint on an unrelated table produce a false positive
    for a table whose own constraint did not actually satisfy the check.
    ``pg_catalog``'s OIDs make that collision structurally impossible.

    Restricted to single-column foreign keys (``array_length(conkey, 1) =
    1``), matching every FK this schema (HRP-54) currently declares; a
    genuinely composite FK on one of these tables would not be recognized
    by this check and is out of scope until the schema needs one.

    A clean (all-``True``) result proves the schema still enforces this
    referential integrity at the database level. It does not prove data
    already violating it before the constraint existed -- see
    ``find_orphaned_dependent_rows`` for that.
    """

    cursor.execute(
        "SELECT c.conrelid::regclass::text "
        "FROM pg_constraint c "
        "WHERE c.contype = 'f' "
        "  AND c.conrelid = ANY(%s::regclass[]) "
        "  AND array_length(c.conkey, 1) = 1 "
        "  AND array_length(c.confkey, 1) = 1 "
        "  AND c.confrelid = 'employees'::regclass "
        "  AND (SELECT attname FROM pg_attribute "
        "       WHERE attrelid = c.conrelid AND attnum = c.conkey[1]) = 'employee_id' "
        "  AND (SELECT attname FROM pg_attribute "
        "       WHERE attrelid = c.confrelid AND attnum = c.confkey[1]) = 'id'",
        [list(tables)],
    )
    tables_with_fk = {row[0] for row in cursor.fetchall()}
    return {table: table in tables_with_fk for table in tables}


def find_orphaned_dependent_rows(cursor: psycopg.Cursor[Any]) -> dict[str, tuple[int, ...]]:
    """Find dependent-table rows whose ``employee_id`` has no matching row
    in ``employees``.

    A clean (all-empty) result proves no dependent row is currently
    orphaned. It relies on the FK constraint from
    ``check_foreign_key_constraints_present`` still being present; it says
    nothing about future inserts.
    """

    orphans: dict[str, tuple[int, ...]] = {}
    for table in DEPENDENT_TABLES:
        query = sql.SQL(
            "SELECT t.id FROM {table} t "
            "WHERE NOT EXISTS (SELECT 1 FROM employees e WHERE e.id = t.employee_id)"
        ).format(table=sql.Identifier(table))
        cursor.execute(query)
        orphans[table] = tuple(row[0] for row in cursor.fetchall())
    return orphans


def find_incomplete_employees(cursor: psycopg.Cursor[Any]) -> dict[int, tuple[str, ...]]:
    """Find employees with zero rows in one or more dependent tables.

    Informational, not a pass/fail signal by itself: an incomplete
    component is an expected, documented HRP-50 outcome (a domain that
    genuinely never arrived), not necessarily a defect.
    """

    count_expressions = [
        sql.SQL("(SELECT count(*) FROM {table} d WHERE d.employee_id = e.id) AS {alias}").format(
            table=sql.Identifier(table), alias=sql.Identifier(table)
        )
        for table in DEPENDENT_TABLES
    ]
    query = sql.SQL("SELECT e.id, {counts} FROM employees e").format(
        counts=sql.SQL(", ").join(count_expressions)
    )
    cursor.execute(query)

    incomplete: dict[int, tuple[str, ...]] = {}
    for row in cursor.fetchall():
        employee_id = row[0]
        missing = tuple(
            table for table, count in zip(DEPENDENT_TABLES, row[1:], strict=True) if count == 0
        )
        if missing:
            incomplete[employee_id] = missing
    return incomplete


def find_exact_duplicate_dependent_rows(
    cursor: psycopg.Cursor[Any],
) -> dict[str, tuple[tuple[Any, ...], ...]]:
    """Find two or more rows in the same dependent table, same
    ``employee_id``, identical on every non-id column.

    A clean (all-empty) result proves HRP-57's NULL-safe full-column
    exact-match enrichment check has not been bypassed for the inspected
    data. It says nothing about a ``source_reference`` that was never
    reprocessed.
    """

    duplicates: dict[str, tuple[tuple[Any, ...], ...]] = {}
    for table in DEPENDENT_TABLES:
        columns = _DEPENDENT_TABLE_COLUMNS[table]
        group_columns = [sql.Identifier("employee_id"), *(sql.Identifier(c) for c in columns)]
        query = sql.SQL(
            "SELECT {group_columns}, count(*) FROM {table} "
            "GROUP BY {group_columns} HAVING count(*) > 1"
        ).format(
            group_columns=sql.SQL(", ").join(group_columns),
            table=sql.Identifier(table),
        )
        cursor.execute(query)
        duplicates[table] = tuple(tuple(row[:-1]) for row in cursor.fetchall())
    return duplicates


def find_duplicate_processing_audit_references(cursor: psycopg.Cursor[Any]) -> tuple[str, ...]:
    """Find non-null ``raw_event_ref`` values recorded more than once in
    ``processing_audit``.

    A clean (empty) result proves HRP-58's unique index on
    ``raw_event_ref`` has not been dropped or bypassed. It says nothing
    about values recorded before the index existed.
    """

    cursor.execute(
        "SELECT raw_event_ref FROM processing_audit "
        "WHERE raw_event_ref IS NOT NULL "
        "GROUP BY raw_event_ref HAVING count(*) > 1"
    )
    return tuple(row[0] for row in cursor.fetchall())


def count_employees_missing_each_domain(cursor: psycopg.Cursor[Any]) -> dict[str, int]:
    """Count, per dependent table, how many employees currently have zero
    rows there -- computed entirely as PostgreSQL aggregates (one row, one
    ``NOT EXISTS``-filtered ``count(*)`` per domain), never materializing a
    per-employee result to reduce in Python. See HRP-86's spec: this answers
    "how many employees are missing each domain", a different, cheaper
    access pattern than ``find_incomplete_employees()``'s "which employees
    are missing which domains".

    Informational, not a pass/fail signal by itself: a missing domain is an
    expected, documented HRP-50 outcome (a domain that genuinely never
    arrived), not necessarily a defect.
    """

    filters = [
        sql.SQL(
            "count(*) FILTER (WHERE NOT EXISTS ("
            "SELECT 1 FROM {table} d WHERE d.employee_id = e.id)) AS {alias}"
        ).format(table=sql.Identifier(table), alias=sql.Identifier(table))
        for table in DEPENDENT_TABLES
    ]
    query = sql.SQL("SELECT {filters} FROM employees e").format(filters=sql.SQL(", ").join(filters))
    cursor.execute(query)
    result = cursor.fetchone()
    assert result is not None
    return dict(zip(DEPENDENT_TABLES, (int(value) for value in result), strict=True))


def count_rows_per_table(cursor: psycopg.Cursor[Any]) -> dict[str, int]:
    """Return a row count for every curated table, for a quick manual
    sanity snapshot. Proves nothing about the correctness of the data
    itself.
    """

    tables = ("employees", *DEPENDENT_TABLES, "processing_audit")
    counts: dict[str, int] = {}
    for table in tables:
        query = sql.SQL("SELECT count(*) FROM {table}").format(table=sql.Identifier(table))
        cursor.execute(query)
        result = cursor.fetchone()
        assert result is not None
        counts[table] = int(result[0])
    return counts
