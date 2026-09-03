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


def repository_with_mock_connection(
    *, already_processed: bool = False
) -> tuple[PersonRepository, MagicMock, MagicMock]:
    """Build a repository over a mocked connection/cursor.

    ``fetchone()`` now serves two different queries per insert (HRP-58's
    ``processing_audit`` idempotency check, then the ``employees`` insert's
    ``RETURNING id``), so its return value is routed by inspecting the most
    recently executed query instead of a single fixed return value.
    """

    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor

    def fetchone_side_effect() -> tuple[int] | None:
        last_call = mock_cursor.execute.call_args
        query_text = str(last_call.args[0]) if last_call is not None else ""
        if "processing_audit" in query_text and "SELECT" in query_text.upper():
            return (1,) if already_processed else None
        return (42,)

    mock_cursor.fetchone.side_effect = fetchone_side_effect
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
    # HRP-58 check + employees insert + one locations insert + audit insert
    assert mock_cursor.execute.call_count == 4
    check_call, employees_call, locations_call, audit_call = mock_cursor.execute.call_args_list
    assert "processing_audit" in str(check_call.args[0])
    assert "processing_audit" in str(audit_call.args[0])
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
    # HRP-58 check + employees insert + 2 locations + audit insert
    assert mock_cursor.execute.call_count == 5
    for call in mock_cursor.execute.call_args_list[2:4]:  # the 2 locations inserts only
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

    employees_call = mock_cursor.execute.call_args_list[1]  # index 0 is the HRP-58 check
    bound_values = employees_call.args[1]
    sex_index = list(employee_row(sex=["X"]).fields.keys()).index("sex")
    sex_value = bound_values[sex_index]

    assert isinstance(sex_value, Jsonb)
    assert sex_value.obj == ["X"]


def test_non_jsonb_fields_are_bound_unwrapped() -> None:
    repository, _mock_connection, mock_cursor = repository_with_mock_connection()
    record = mapping(employees=(employee_row(passport="P-001"),))

    repository.insert_mapping(record)

    bound_values = mock_cursor.execute.call_args_list[1].args[1]  # index 0 is the HRP-58 check
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

    # caplog.text renders each record the way a real handler would, including
    # any traceback a future `exc_info=True` might attach -- unlike checking
    # only `record.message`, which would stay clean even if exc_info leaked
    # the sensitive marker through the formatted traceback.
    assert sensitive_marker not in caplog.text
    assert "FakeDatabaseError" in caplog.text
    assert "23505" in caplog.text
    assert all(record_.exc_info is None for record_ in caplog.records)
    mock_connection.rollback.assert_called_once()
    mock_connection.commit.assert_not_called()


# ---------------------------------------------------------------------------
# HRP-56 review fix 3: stronger transaction evidence across all four
# dependent tables, and isolation between components.
# ---------------------------------------------------------------------------


def test_dependent_insert_failure_after_employee_insert_rolls_back_without_commit() -> None:
    repository, mock_connection, mock_cursor = repository_with_mock_connection()
    # 1st call: HRP-58 check succeeds. 2nd call: employees insert succeeds.
    # 3rd call: the dependent (locations) insert fails.
    mock_cursor.execute.side_effect = [None, None, Exception("dependent insert failed")]
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
    # HRP-58 check + employees insert + 4 dependents + audit insert
    assert mock_cursor.execute.call_count == 7
    dependent_calls = mock_cursor.execute.call_args_list[2:-1]  # exclude check/employees/audit

    # Render each composed query to real SQL text (not the object's repr) so
    # the table name can be matched exactly, and key by that table instead of
    # substring-matching, so a bug that inserted into the same table twice
    # (instead of covering all four) would fail this assertion.
    calls_by_table = {call.args[0].as_string(None).split('"')[1]: call for call in dependent_calls}
    assert calls_by_table.keys() == {
        "locations",
        "professional_profiles",
        "bank_accounts",
        "network_data",
    }

    assert calls_by_table["locations"].args[1] == [42, "Ada Example", "Springfield"]
    assert calls_by_table["professional_profiles"].args[1] == [42, "Ada Example", "Engineer"]
    assert calls_by_table["bank_accounts"].args[1] == [42, "ES00-0000-0000-0000"]
    assert calls_by_table["network_data"].args[1] == [42, "10.0.0.1"]
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


# ---------------------------------------------------------------------------
# HRP-58: skip already-processed components by source_reference, without any
# person-identity field involved.
# ---------------------------------------------------------------------------


def test_already_processed_component_is_skipped_without_any_write() -> None:
    repository, mock_connection, mock_cursor = repository_with_mock_connection(
        already_processed=True
    )
    record = mapping(employees=(employee_row(),), locations=(location_row(),))

    outcome = repository.insert_mapping(record)

    assert outcome.inserted is False
    assert outcome.employee_id is None
    assert outcome.skipped_reason == "already_processed"
    # Only the check itself ran; no employees/dependent INSERT was attempted.
    assert mock_cursor.execute.call_count == 1
    assert "processing_audit" in str(mock_cursor.execute.call_args_list[0].args[0])
    mock_connection.commit.assert_called_once()  # closes the read-only check
    mock_connection.rollback.assert_not_called()


def test_new_component_records_a_processing_audit_row_with_the_source_reference() -> None:
    repository, mock_connection, mock_cursor = repository_with_mock_connection()
    record = mapping(employees=(employee_row(),))

    outcome = repository.insert_mapping(record)

    assert outcome.inserted is True
    # HRP-58 check + employees insert + processing_audit insert
    assert mock_cursor.execute.call_count == 3
    audit_call = mock_cursor.execute.call_args_list[2]
    assert "processing_audit" in str(audit_call.args[0])
    assert "INSERT" in str(audit_call.args[0]).upper()
    employee_id, stage, status, raw_event_ref = audit_call.args[1]
    assert employee_id == 42
    assert stage == "insert"
    assert status == "inserted"
    assert raw_event_ref == employee_row().source_reference == "p"
    mock_connection.commit.assert_called_once()


def test_already_processed_check_never_binds_a_business_identity_value() -> None:
    repository, _mock_connection, mock_cursor = repository_with_mock_connection()
    record = mapping(employees=(employee_row(passport="SHOULD-NOT-APPEAR-IN-CHECK"),))

    repository.insert_mapping(record)

    check_call = mock_cursor.execute.call_args_list[0]
    assert check_call.args[1] == ["p"]  # only the opaque source_reference is bound
    assert "SHOULD-NOT-APPEAR-IN-CHECK" not in check_call.args[1]
    assert "passport" not in str(check_call.args[0]).lower()
