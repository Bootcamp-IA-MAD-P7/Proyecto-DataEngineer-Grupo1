"""Behavior tests for the HRP-56 PersonRecordMapping -> PostgreSQL repository."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest
from psycopg.types.json import Jsonb

from hr_pro_platform.storage.person_mapper import CandidateRow, PersonRecordMapping
from hr_pro_platform.storage.person_repository import PersonRepository


def employee_row(passport: str = "P-001", sex: list[str] | None = None) -> CandidateRow:
    fields: dict[str, object] = {
        "first_name": "Ada",
        "last_name": "Example",
        "passport": passport,
    }
    if sex is not None:
        fields["sex"] = sex
    return CandidateRow(table="employees", group_key=passport, fields=fields, source_reference="p")


def location_row(city: str = "Springfield") -> CandidateRow:
    return CandidateRow(
        table="locations",
        group_key="Ada Example",
        fields={"full_name": "Ada Example", "city": city},
        source_reference="l",
    )


def professional_row() -> CandidateRow:
    return CandidateRow(
        table="professional_profiles",
        group_key="Ada Example",
        fields={"full_name": "Ada Example", "job": "Engineer"},
        source_reference="w",
    )


def bank_row() -> CandidateRow:
    return CandidateRow(
        table="bank_accounts",
        group_key="P-001",
        fields={"iban": "ES00-0000-0000-0000"},
        source_reference="b",
    )


def net_row() -> CandidateRow:
    return CandidateRow(
        table="network_data",
        group_key="A-1",
        fields={"ip_v4": "10.0.0.1"},
        source_reference="n",
    )


def mapping(
    *,
    employees: tuple[CandidateRow, ...] = (),
    locations: tuple[CandidateRow, ...] = (),
    professional_profiles: tuple[CandidateRow, ...] = (),
    bank_accounts: tuple[CandidateRow, ...] = (),
    network_data: tuple[CandidateRow, ...] = (),
) -> PersonRecordMapping:
    return PersonRecordMapping(
        status="complete",
        correlation_rules=(),
        provenance=(),
        employees=employees,
        locations=locations,
        professional_profiles=professional_profiles,
        bank_accounts=bank_accounts,
        network_data=network_data,
    )


def repository_with_mock_connection() -> tuple[PersonRepository, MagicMock, MagicMock]:
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (42,)
    mock_connection = MagicMock()
    mock_connection.cursor.return_value = mock_cursor

    repository = PersonRepository()
    repository._connection = mock_connection
    return repository, mock_connection, mock_cursor


def test_single_employee_row_is_inserted_and_id_propagated_to_dependents() -> None:
    repository, mock_connection, mock_cursor = repository_with_mock_connection()
    record = mapping(employees=(employee_row(),), locations=(location_row(),))

    outcome = repository.insert_mapping(record)

    assert outcome.inserted is True
    assert outcome.employee_id == 42
    assert mock_cursor.execute.call_count == 2  # one employees insert, one locations insert
    employees_call, locations_call = mock_cursor.execute.call_args_list
    assert "employees" in str(employees_call.args[0])
    assert "RETURNING id" in str(employees_call.args[0])
    assert "locations" in str(locations_call.args[0])
    assert locations_call.args[1][0] == 42  # employee_id is the first bound value
    mock_connection.commit.assert_called_once()
    mock_connection.rollback.assert_not_called()


def test_multiple_dependent_rows_in_one_table_share_the_same_employee_id() -> None:
    repository, mock_connection, mock_cursor = repository_with_mock_connection()
    record = mapping(
        employees=(employee_row(),),
        locations=(location_row("Springfield"), location_row("Shelbyville")),
    )

    outcome = repository.insert_mapping(record)

    assert outcome.inserted is True
    assert mock_cursor.execute.call_count == 3  # employees + 2 locations
    for call in mock_cursor.execute.call_args_list[1:]:
        assert call.args[1][0] == 42
    mock_connection.commit.assert_called_once()


def test_zero_employee_rows_are_skipped_without_any_insert() -> None:
    repository, mock_connection, mock_cursor = repository_with_mock_connection()
    record = mapping(employees=(), locations=(location_row(),))

    outcome = repository.insert_mapping(record)

    assert outcome.inserted is False
    assert outcome.employee_id is None
    assert outcome.skipped_reason == "no_personal_domain"
    mock_cursor.execute.assert_not_called()
    mock_connection.commit.assert_not_called()


def test_ambiguous_personal_domain_is_skipped_without_any_insert() -> None:
    repository, mock_connection, mock_cursor = repository_with_mock_connection()
    record = mapping(
        employees=(employee_row("P-001"), employee_row("P-002")),
        locations=(location_row(),),
    )

    outcome = repository.insert_mapping(record)

    assert outcome.inserted is False
    assert outcome.employee_id is None
    assert outcome.skipped_reason == "ambiguous_personal_domain"
    mock_cursor.execute.assert_not_called()
    mock_connection.commit.assert_not_called()


# ---------------------------------------------------------------------------
# HRP-56 review fix 1: employees.sex must be adapted as JSONB, not sent as a
# plain Python list.
# ---------------------------------------------------------------------------


def test_employees_sex_is_bound_as_jsonb() -> None:
    repository, _mock_connection, mock_cursor = repository_with_mock_connection()
    record = mapping(employees=(employee_row(sex=["X"]),))

    repository.insert_mapping(record)

    employees_call = mock_cursor.execute.call_args_list[0]
    bound_values = employees_call.args[1]
    sex_index = list(employee_row(sex=["X"]).fields.keys()).index("sex")
    sex_value = bound_values[sex_index]

    assert isinstance(sex_value, Jsonb)
    assert sex_value.obj == ["X"]


def test_non_jsonb_fields_are_bound_unwrapped() -> None:
    repository, _mock_connection, mock_cursor = repository_with_mock_connection()
    record = mapping(employees=(employee_row(passport="P-001"),))

    repository.insert_mapping(record)

    bound_values = mock_cursor.execute.call_args_list[0].args[1]
    assert "P-001" in bound_values
    assert not any(isinstance(value, Jsonb) for value in bound_values)


# ---------------------------------------------------------------------------
# HRP-56 review fix 2: failure logging must not leak database error text.
# ---------------------------------------------------------------------------


def test_insert_failure_logs_only_error_class_and_sqlstate_not_error_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    repository, mock_connection, mock_cursor = repository_with_mock_connection()
    sensitive_marker = "SENSITIVE-VALUE-MARKER-DO-NOT-LOG"

    class FakeDatabaseError(Exception):
        sqlstate = "23505"

    mock_cursor.execute.side_effect = FakeDatabaseError(
        f"duplicate key value violates unique constraint: {sensitive_marker}"
    )
    record = mapping(employees=(employee_row(),))

    with caplog.at_level(logging.ERROR):
        with pytest.raises(FakeDatabaseError):
            repository.insert_mapping(record)

    log_text = "\n".join(record_.message for record_ in caplog.records)
    assert sensitive_marker not in log_text
    assert "FakeDatabaseError" in log_text
    assert "23505" in log_text
    mock_connection.rollback.assert_called_once()
    mock_connection.commit.assert_not_called()


# ---------------------------------------------------------------------------
# HRP-56 review fix 3: stronger transaction evidence across all four
# dependent tables, and isolation between components.
# ---------------------------------------------------------------------------


def test_dependent_insert_failure_after_employee_insert_rolls_back_without_commit() -> None:
    repository, mock_connection, mock_cursor = repository_with_mock_connection()
    mock_cursor.execute.side_effect = [None, Exception("dependent insert failed")]
    record = mapping(employees=(employee_row(),), locations=(location_row(),))

    with pytest.raises(Exception, match="dependent insert failed"):
        repository.insert_mapping(record)

    mock_connection.rollback.assert_called_once()
    mock_connection.commit.assert_not_called()


def test_employee_id_propagates_correctly_to_all_four_dependent_tables() -> None:
    repository, mock_connection, mock_cursor = repository_with_mock_connection()
    record = mapping(
        employees=(employee_row(),),
        locations=(location_row(),),
        professional_profiles=(professional_row(),),
        bank_accounts=(bank_row(),),
        network_data=(net_row(),),
    )

    outcome = repository.insert_mapping(record)

    assert outcome.employee_id == 42
    assert mock_cursor.execute.call_count == 5  # employees + 4 dependents
    dependent_calls = mock_cursor.execute.call_args_list[1:]
    assert len(dependent_calls) == 4
    for call in dependent_calls:
        query_text = str(call.args[0])
        bound_values = call.args[1]
        assert bound_values[0] == 42
        if "locations" in query_text:
            assert "Ada Example" in bound_values
        elif "professional_profiles" in query_text:
            assert "Engineer" in bound_values
        elif "bank_accounts" in query_text:
            assert "ES00-0000-0000-0000" in bound_values
        elif "network_data" in query_text:
            assert "10.0.0.1" in bound_values
        else:
            pytest.fail(f"unexpected dependent table in query: {query_text}")
    mock_connection.commit.assert_called_once()


def test_insert_mappings_isolates_a_failure_to_its_own_component() -> None:
    repository, mock_connection, mock_cursor = repository_with_mock_connection()
    good_record = mapping(employees=(employee_row("P-001"),))
    bad_record = mapping(employees=(employee_row("P-002"),))

    call_count = 0

    def execute_side_effect(*args: object, **kwargs: object) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("db error on first component")

    mock_cursor.execute.side_effect = execute_side_effect

    outcomes = repository.insert_mappings([bad_record, good_record])

    assert outcomes[0].inserted is False
    assert outcomes[0].skipped_reason == "insert_error"
    assert outcomes[1].inserted is True
    assert outcomes[1].employee_id == 42
    assert mock_connection.rollback.call_count == 1
    assert mock_connection.commit.call_count == 1
