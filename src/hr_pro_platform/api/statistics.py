"""Read-only aggregate statistics over curated PostgreSQL data.

See docs/specs/HRP-86-statistics-endpoint.md. Reuses
``storage/validation_queries.py``'s existing safe aggregate functions
(``count_rows_per_table``, ``find_incomplete_employees``) instead of writing
new ad-hoc SQL: both already avoid the row-multiplication risk of joining
``employees`` to a 1:N dependent table, using ``COUNT(*)`` per table or a
correlated subquery, never a ``JOIN`` + ``COUNT``/``DISTINCT``.

Only aggregate counts are returned here -- never an individual
``employee_id`` or a dependent-table column value (e.g. no ``iban``/``salary``
from ``bank_accounts``), consistent with HRP-84/85's exclusion of per-record
financial data from their responses.
"""

from __future__ import annotations

from typing import Any

import psycopg
from pydantic import BaseModel

from ..storage.validation_queries import (
    DEPENDENT_TABLES,
    count_rows_per_table,
    find_incomplete_employees,
)


class StatisticsResult(BaseModel):
    rows_per_table: dict[str, int]
    employees_missing_domain: dict[str, int]


def compute_statistics(cursor: psycopg.Cursor[Any]) -> StatisticsResult:
    """Compute the aggregate statistics served by ``GET /statistics``.

    ``employees_missing_domain`` counts, per dependent table, how many
    employees currently have zero rows there. It is derived from
    ``find_incomplete_employees()``, which documents a missing domain as an
    expected HRP-50 outcome, not necessarily a defect -- this endpoint makes
    no completeness claim about any individual person, and returns no
    ``employee_id``, only the aggregate count.
    """

    rows_per_table = count_rows_per_table(cursor)
    incomplete = find_incomplete_employees(cursor)

    employees_missing_domain: dict[str, int] = dict.fromkeys(DEPENDENT_TABLES, 0)
    for missing_tables in incomplete.values():
        for table in missing_tables:
            employees_missing_domain[table] += 1

    return StatisticsResult(
        rows_per_table=rows_per_table,
        employees_missing_domain=employees_missing_domain,
    )


__all__ = ["StatisticsResult", "compute_statistics"]
