"""Read-only person search over curated PostgreSQL data.

See docs/specs/HRP-84-search-person-endpoint.md. Every query here uses
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

from collections.abc import Mapping
from typing import Any

import psycopg
from psycopg import sql
from pydantic import BaseModel

# Every filterable employees column HRP-84 allows, mapped to the exact
# column name -- used only as a fixed, code-controlled allowlist for
# sql.Identifier(), never built from caller-supplied key names.
ALLOWED_FILTERS: frozenset[str] = frozenset({"id", "passport", "first_name", "last_name"})

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
    employee_rows = cursor.fetchall()

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
