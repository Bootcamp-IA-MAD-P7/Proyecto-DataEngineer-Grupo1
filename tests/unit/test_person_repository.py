"""Behavior tests for the HRP-56 PersonRecordMapping -> PostgreSQL repository."""

from __future__ import annotations

from unittest.mock import MagicMock

from hr_pro_platform.storage.person_mapper import CandidateRow, PersonRecordMapping
from hr_pro_platform.storage.person_repository import PersonRepository


def employee_row(passport: str = "P-001") -> CandidateRow:
    return CandidateRow(
        table="employees",
        group_key=passport,
        fields={"first_name": "Ada", "last_name": "Example", "passport": passport},
        source_reference="p",
    )


def location_row(city: str = "Springfield") -> CandidateRow:
    return CandidateRow(
        table="locations",
        group_key="Ada Example",
        fields={"full_name": "Ada Example", "city": city},
        source_reference="l",
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


def test_a_failed_insert_rolls_back_the_whole_component() -> None:
    repository, mock_connection, mock_cursor = repository_with_mock_connection()
    mock_cursor.execute.side_effect = Exception("db error")
    record = mapping(employees=(employee_row(),), locations=(location_row(),))

    try:
        repository.insert_mapping(record)
    except Exception:
        pass

    mock_connection.rollback.assert_called_once()
    mock_connection.commit.assert_not_called()


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
