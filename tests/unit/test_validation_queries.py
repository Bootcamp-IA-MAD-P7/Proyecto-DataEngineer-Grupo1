"""Unit tests for storage/validation_queries.py's "duplicate found" and
"constraint missing" positive paths, which cannot be produced against a
real database because the schema's own constraints (HRP-54/58) forbid
them by construction. See tests/integration/test_validation_queries.py
for the real-database evidence of the "clean" negative paths.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from hr_pro_platform.storage.validation_queries import (
    check_foreign_key_constraints_present,
    count_employees_missing_each_domain,
    find_duplicate_processing_audit_references,
    find_exact_duplicate_dependent_rows,
)


def _query_text(query: object) -> str:
    as_string = getattr(query, "as_string", None)
    return as_string(None) if callable(as_string) else str(query)


def test_check_foreign_key_constraints_present_reports_a_missing_constraint() -> None:
    cursor = MagicMock()
    # Only "locations" and "bank_accounts" have a reported FK constraint --
    # simulating a schema regression where "professional_profiles" and
    # "network_data" lost theirs.
    cursor.fetchall.return_value = [("locations",), ("bank_accounts",)]

    result = check_foreign_key_constraints_present(cursor)

    assert result == {
        "locations": True,
        "professional_profiles": False,
        "bank_accounts": True,
        "network_data": False,
    }


def test_find_duplicate_processing_audit_references_returns_the_duplicated_values() -> None:
    cursor = MagicMock()
    cursor.fetchall.return_value = [("ref-a",), ("ref-b",)]

    result = find_duplicate_processing_audit_references(cursor)

    assert result == ("ref-a", "ref-b")
    query_text = _query_text(cursor.execute.call_args.args[0])
    assert "raw_event_ref IS NOT NULL" in query_text
    assert "HAVING count(*) > 1" in query_text


def test_find_exact_duplicate_dependent_rows_groups_by_employee_id_and_every_column() -> None:
    cursor = MagicMock()
    # One duplicated pair for "locations" (count=2, stripped from the
    # returned tuple), no duplicates for the other three tables.
    cursor.fetchall.side_effect = [
        [(7, "Full Name", "City", "Address", None, 2)],
        [],
        [],
        [],
    ]

    result = find_exact_duplicate_dependent_rows(cursor)

    assert result["locations"] == ((7, "Full Name", "City", "Address", None),)
    assert result["professional_profiles"] == ()
    assert result["bank_accounts"] == ()
    assert result["network_data"] == ()

    locations_query_text = _query_text(cursor.execute.call_args_list[0].args[0])
    assert '"employee_id"' in locations_query_text
    assert '"full_name"' in locations_query_text
    assert '"city"' in locations_query_text
    assert '"address"' in locations_query_text
    assert '"ip_v4"' in locations_query_text
    assert "GROUP BY" in locations_query_text
    assert "HAVING count(*) > 1" in locations_query_text


def test_count_employees_missing_each_domain_maps_one_aggregate_row_by_table_order() -> None:
    cursor = MagicMock()
    # One row, four counts, in DEPENDENT_TABLES order
    # (locations, professional_profiles, bank_accounts, network_data).
    cursor.fetchone.return_value = (3, 5, 0, 2)

    result = count_employees_missing_each_domain(cursor)

    assert result == {
        "locations": 3,
        "professional_profiles": 5,
        "bank_accounts": 0,
        "network_data": 2,
    }
    # A single query, computed as PostgreSQL aggregates -- never a JOIN
    # (which would multiply rows across the 1:N dependent tables) and never
    # a per-employee fetchall.
    assert cursor.execute.call_count == 1
    query_text = _query_text(cursor.execute.call_args.args[0])
    assert "NOT EXISTS" in query_text
    assert "FILTER" in query_text
    assert "JOIN" not in query_text
    cursor.fetchall.assert_not_called()
