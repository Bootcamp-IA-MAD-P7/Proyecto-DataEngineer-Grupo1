"""Read-only person search over curated PostgreSQL data.

See docs/specs/HRP-84-search-person-endpoint.md and
docs/specs/HRP-85-search-by-location-profession.md. Every query here uses
``psycopg``'s ``sql.SQL``/``sql.Identifier``/``sql.Placeholder``, never
raw string interpolation, matching ``person_repository.py`` and
``validation_queries.py``'s existing convention.

``bank_accounts`` is deliberately excluded from every response here --
the project has no authentication/authorization layer yet, and nothing
in the approved data contract explicitly authorizes exposing financial
fields (``iban``/``salary``) through this endpoint. See the spec's
"Open decision" section.

No query here asserts or resolves real-world person identity;
ADR-0006 (person correlation key) remains "Accepted in principle", not
final. A match is an exact-equality lookup against already-curated
technical fields, nothing more.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import psycopg
from psycopg import sql
from pydantic import BaseModel

# Every filterable employees column HRP-84 allows, mapped to the exact
# column name -- used only as a fixed, code-controlled allowlist for
# sql.Identifier(), never built from caller-supplied key names.
ALLOWED_FILTERS: frozenset[str] = frozenset({"id", "passport", "first_name", "last_name"})

# HRP-85: filterable columns on locations/professional_profiles. Kept
# separate from ALLOWED_FILTERS because these live on a different table
# than `employees` -- see docs/specs/HRP-85-search-by-location-profession.md
# ("Decisions confirmed", item 1).
LOCATION_FILTERS: frozenset[str] = frozenset({"city", "address"})
PROFESSIONAL_FILTERS: frozenset[str] = frozenset({"job", "company"})

_EMPLOYEE_COLUMNS: tuple[str, ...] = (
    "id",
    "first_name",
    "last_name",
    "sex",
    "telephone_number",
    "email",
    "passport",
)
_LOCATION_COLUMNS: tuple[str, ...] = ("full_name", "city", "address", "ip_v4")
_PROFESSIONAL_PROFILE_COLUMNS: tuple[str, ...] = (
    "full_name",
    "company",
    "company_address",
    "company_email",
    "company_telephone_number",
    "job",
)


class LocationResult(BaseModel):
    full_name: str | None = None
    city: str | None = None
    address: str | None = None
    ip_v4: str | None = None


class ProfessionalProfileResult(BaseModel):
    full_name: str | None = None
    company: str | None = None
    company_address: str | None = None
    company_email: str | None = None
    company_telephone_number: str | None = None
    job: str | None = None


class PersonSearchResult(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    sex: list[str] | None = None
    telephone_number: str | None = None
    email: str | None = None
    passport: str | None = None
    locations: list[LocationResult] = []
    professional_profiles: list[ProfessionalProfileResult] = []


def search_employees(
    cursor: psycopg.Cursor[Any],
    *,
    filters: Mapping[str, object],
    limit: int,
    offset: int,
) -> list[PersonSearchResult]:
    """Search ``employees`` by exact-match filters and attach each
    match's ``locations``/``professional_profiles`` rows.

    ``filters`` keys must already be validated against
    ``ALLOWED_FILTERS`` by the caller (the API route) before this is
    called -- this function trusts that allowlisting, not the raw
    query-string key names.
    """

    conditions = [
        sql.SQL("{column} = {placeholder}").format(
            column=sql.Identifier(name), placeholder=sql.Placeholder()
        )
        for name in filters
    ]
    query = sql.SQL(
        "SELECT {columns} FROM employees WHERE {conditions} "
        "ORDER BY id LIMIT {limit} OFFSET {offset}"
    ).format(
        columns=sql.SQL(", ").join(sql.Identifier(column) for column in _EMPLOYEE_COLUMNS),
        conditions=sql.SQL(" AND ").join(conditions),
        limit=sql.Placeholder(),
        offset=sql.Placeholder(),
    )
    cursor.execute(query, [*filters.values(), limit, offset])
    return _assemble_results(cursor, cursor.fetchall())


def search_employees_by_location_or_profession(
    cursor: psycopg.Cursor[Any],
    *,
    location_filters: Mapping[str, object],
    professional_filters: Mapping[str, object],
    limit: int,
    offset: int,
) -> list[PersonSearchResult]:
    """Search employees by an exact-match ``locations``/``professional_profiles``
    filter (HRP-85).

    ``location_filters``/``professional_filters`` keys must already be
    validated by the caller against ``LOCATION_FILTERS``/
    ``PROFESSIONAL_FILTERS``; at least one of the two mappings must be
    non-empty. When both are supplied, a matching employee must satisfy
    both (AND) -- see docs/specs/HRP-85-search-by-location-profession.md
    ("Decisions confirmed", item 3).
    """

    id_sets: list[set[int]] = []
    if location_filters:
        id_sets.append(_matching_employee_ids(cursor, "locations", location_filters))
    if professional_filters:
        id_sets.append(
            _matching_employee_ids(cursor, "professional_profiles", professional_filters)
        )
    employee_ids = set.intersection(*id_sets)
    if not employee_ids:
        return []

    query = sql.SQL(
        "SELECT {columns} FROM employees WHERE id = ANY({ids}) "
        "ORDER BY id LIMIT {limit} OFFSET {offset}"
    ).format(
        columns=sql.SQL(", ").join(sql.Identifier(column) for column in _EMPLOYEE_COLUMNS),
        ids=sql.Placeholder(),
        limit=sql.Placeholder(),
        offset=sql.Placeholder(),
    )
    cursor.execute(query, [list(employee_ids), limit, offset])
    return _assemble_results(cursor, cursor.fetchall())


def _matching_employee_ids(
    cursor: psycopg.Cursor[Any], table: str, filters: Mapping[str, object]
) -> set[int]:
    """Return the distinct ``employee_id``s whose row in ``table`` matches
    every supplied filter (AND)."""

    conditions = [
        sql.SQL("{column} = {placeholder}").format(
            column=sql.Identifier(name), placeholder=sql.Placeholder()
        )
        for name in filters
    ]
    query = sql.SQL("SELECT DISTINCT employee_id FROM {table} WHERE {conditions}").format(
        table=sql.Identifier(table),
        conditions=sql.SQL(" AND ").join(conditions),
    )
    cursor.execute(query, list(filters.values()))
    return {row[0] for row in cursor.fetchall()}


def _assemble_results(
    cursor: psycopg.Cursor[Any], employee_rows: Sequence[Any]
) -> list[PersonSearchResult]:
    """Build one ``PersonSearchResult`` per matched ``employees`` row,
    attaching its ``locations``/``professional_profiles`` rows. Shared by
    every search entry point so every response has the same shape
    regardless of which filter found the employee."""

    results: list[PersonSearchResult] = []
    for row in employee_rows:
        employee_id = row[0]
        results.append(
            PersonSearchResult(
                id=employee_id,
                first_name=row[1],
                last_name=row[2],
                sex=row[3],
                telephone_number=row[4],
                email=row[5],
                passport=row[6],
                locations=_fetch_dependent(
                    cursor, "locations", _LOCATION_COLUMNS, employee_id, LocationResult
                ),
                professional_profiles=_fetch_dependent(
                    cursor,
                    "professional_profiles",
                    _PROFESSIONAL_PROFILE_COLUMNS,
                    employee_id,
                    ProfessionalProfileResult,
                ),
            )
        )
    return results


def _fetch_dependent(
    cursor: psycopg.Cursor[Any],
    table: str,
    columns: tuple[str, ...],
    employee_id: int,
    model: type[LocationResult] | type[ProfessionalProfileResult],
) -> list[Any]:
    query = sql.SQL("SELECT {columns} FROM {table} WHERE employee_id = {employee_id}").format(
        columns=sql.SQL(", ").join(sql.Identifier(column) for column in columns),
        table=sql.Identifier(table),
        employee_id=sql.Placeholder(),
    )
    cursor.execute(query, [employee_id])
    return [model(**dict(zip(columns, row, strict=True))) for row in cursor.fetchall()]
