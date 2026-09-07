"""Read-only aggregate statistics over curated PostgreSQL data.

See docs/specs/HRP-86-statistics-endpoint.md. Reuses
``storage/validation_queries.py``'s existing safe aggregate functions
(``count_rows_per_table``, ``count_employees_missing_each_domain``) instead
of writing new ad-hoc SQL here: both compute their result entirely inside
PostgreSQL (``COUNT(*)`` per table, or a single ``NOT EXISTS``-filtered
aggregate query) and return only the fixed set of integers this endpoint
needs -- no per-employee row is ever materialized or transferred to answer
"how many", only to answer "which" (a different function,
``find_incomplete_employees()``, intentionally not used here).

The response is two explicit Pydantic models, not an unrestricted
``dict[str, int]``: every field name is part of the API contract, visible in
the generated OpenAPI schema, and no per-record value (an ``employee_id``, an
``iban``/``salary`` from ``bank_accounts``, or any other column value) can be
added to either model without a visible, reviewable schema change.
"""

from __future__ import annotations

from typing import Any

import psycopg
from pydantic import BaseModel

from ..storage.validation_queries import count_employees_missing_each_domain, count_rows_per_table


class RowsPerTable(BaseModel):
    employees: int
    locations: int
    professional_profiles: int
    bank_accounts: int
    network_data: int
    processing_audit: int


class EmployeesMissingDomain(BaseModel):
    locations: int
    professional_profiles: int
    bank_accounts: int
    network_data: int


class StatisticsResult(BaseModel):
    rows_per_table: RowsPerTable
    employees_missing_domain: EmployeesMissingDomain


def compute_statistics(cursor: psycopg.Cursor[Any]) -> StatisticsResult:
    """Compute the aggregate statistics served by ``GET /statistics``.

    Both underlying queries return one row of fixed-width integers; nothing
    here iterates over employees in Python.
    """

    return StatisticsResult(
        rows_per_table=RowsPerTable(**count_rows_per_table(cursor)),
        employees_missing_domain=EmployeesMissingDomain(
            **count_employees_missing_each_domain(cursor)
        ),
    )


__all__ = ["EmployeesMissingDomain", "RowsPerTable", "StatisticsResult", "compute_statistics"]
