"""Behavior tests for the HRP-56 PersonRecordMapping -> PostgreSQL repository."""

from __future__ import annotations

import logging
import re
from unittest.mock import MagicMock

import pytest
from psycopg.types.json import Jsonb

from hr_pro_platform.storage.person_mapper import CandidateRow, PersonRecordMapping
from hr_pro_platform.storage.person_repository import _DEPENDENT_TABLE_COLUMNS, PersonRepository


def employee_row(
    passport: str = "P-001", sex: list[str] | None = None, source_reference: str = "p"
) -> CandidateRow:
    fields: dict[str, object] = {
        "first_name": "Ada",
        "last_name": "Example",
        "passport": passport,
    }
    if sex is not None:
        fields["sex"] = sex
    return CandidateRow(
        table="employees", group_key=passport, fields=fields, source_reference=source_reference
    )


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


_DEPENDENT_TABLES = ("locations", "professional_profiles", "bank_accounts", "network_data")


def _query_text(query: object) -> str:
    """Render a query to real SQL text, whether it's a plain string or a
    ``psycopg.sql.Composed`` object (which needs ``.as_string(None)`` --
    plain ``str()`` on a Composed object returns its Python repr, not SQL)."""

    as_string = getattr(query, "as_string", None)
    return as_string(None) if callable(as_string) else str(query)


def _parse_insert_columns(text: str) -> list[str]:
    """Extract the quoted column names from an ``INSERT INTO "t" (...) VALUES``
    statement's real SQL text, in the order they were bound."""

    match = re.search(r"\(([^)]*)\)\s*VALUES", text)
    if not match:
        return []
    return [name.strip().strip('"') for name in match.group(1).split(",")]


def repository_with_mock_connection(
    *, preseeded_source_references: set[str] | None = None
) -> tuple[PersonRepository, MagicMock, MagicMock]:
    """Build a repository over a mocked connection/cursor.

    ``fetchone()`` now serves several different queries per call (HRP-58's
    ``processing_audit`` idempotency check, HRP-57's existing-employee_id
    lookup and dependent-row-exists check, and the ``employees`` insert's
    ``RETURNING id``), so its return value is routed by inspecting the most
    recently executed query's real SQL text (via ``_query_text``) and its
    bound parameters.

    Critically, this is backed by real, mutable state -- recorded
    ``source_reference`` values, the ``employee_id`` recorded for each, and
    the exact dependent rows already "persisted" per ``employee_id`` --
    rather than a single fixed response. This lets a test insert two
    distinct references and confirm only the replayed one is skipped, and
    lets a test confirm that only a genuinely new dependent row is inserted
    on enrichment. A fixed-response mock would pass even if the lookup
    ignored the bound parameters entirely.
    """

    recorded_refs: set[str] = set(preseeded_source_references or ())
    employee_id_by_ref: dict[str, int] = {}
    existing_dependent_keys: set[tuple[str, int, tuple[object, ...]]] = set()

    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor

    def execute_side_effect(query: object, params: list[object] | None = None) -> None:
        text = _query_text(query)
        upper = text.upper()
        if "INSERT INTO PROCESSING_AUDIT" in upper and params:
            employee_id, _stage, _status, raw_event_ref = params
            recorded_refs.add(str(raw_event_ref))
            employee_id_by_ref[str(raw_event_ref)] = int(employee_id)
        elif upper.startswith("INSERT INTO") and "RETURNING" not in upper and params:
            for table in _DEPENDENT_TABLES:
                if f'"{table}"' in text:
                    # Reconstruct the full persisted row shape (all of that
                    # table's columns, absent ones as None) from the actual
                    # column list in the rendered SQL, not just the bound
                    # values in isolation -- this must match the same shape
                    # _dependent_row_exists() queries against (see there).
                    provided = dict(zip(_parse_insert_columns(text), params, strict=True))
                    employee_id = int(provided.pop("employee_id"))
                    full_row = tuple(
                        provided.get(column) for column in _DEPENDENT_TABLE_COLUMNS[table]
                    )
                    existing_dependent_keys.add((table, employee_id, full_row))
                    break

    mock_cursor.execute.side_effect = execute_side_effect

    def fetchone_side_effect() -> tuple[object, ...] | None:
        last_call = mock_cursor.execute.call_args
        text = _query_text(last_call.args[0]) if last_call is not None else ""
        upper = text.upper()
        bound = last_call.args[1] if last_call is not None and len(last_call.args) > 1 else None

        if "SELECT EMPLOYEE_ID FROM PROCESSING_AUDIT" in upper:
            reference = bound[0] if bound else None
            employee_id = employee_id_by_ref.get(str(reference)) if reference is not None else None
            return (employee_id,) if employee_id is not None else None

        if "SELECT 1 FROM PROCESSING_AUDIT" in upper:
            checked_reference = bound[0] if bound else None
            return (1,) if checked_reference in recorded_refs else None

        if upper.startswith("SELECT 1 FROM") and bound:
            for table in _DEPENDENT_TABLES:
                if f'"{table}"' in text:
                    key = (table, int(bound[0]), tuple(bound[1:]))
                    return (1,) if key in existing_dependent_keys else None

        return (42,)  # employees insert's RETURNING id

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
    """A pure replay (no dependent rows at all, e.g. resubmitting the exact
    same Personal-only fragment) still behaves exactly as HRP-58 originally
    defined: a single check, no further lookup or write. HRP-57's
    enrichment path is only entered when there is dependent data to
    consider -- see test_enrichment_* below for that behavior."""

    repository, mock_connection, mock_cursor = repository_with_mock_connection(
        preseeded_source_references={"p"}
    )
    record = mapping(employees=(employee_row(),))

    outcome = repository.insert_mapping(record)

    assert outcome.inserted is False
    assert outcome.employee_id is None
    assert outcome.skipped_reason == "already_processed"
    assert outcome.enriched_tables == ()
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


def test_two_distinct_source_references_both_insert_and_only_the_replay_skips() -> None:
    """Guards against a lookup that ignores the bound source_reference.

    Both fixtures deliberately share identical business fields (same
    passport, same name) -- only ``source_reference`` differs -- so the
    behavioral assertions below would fail if the mocked "already processed"
    lookup incorrectly matched any recorded processing_audit row instead of
    the specific one requested.

    A mock cannot verify actual SQL filtering correctness -- only a real
    database can (see the equivalent two-reference scenario in
    tests/integration/test_person_repository.py, which is what actually
    proves the WHERE clause filters correctly). This test additionally
    asserts the check statement's literal SQL text includes the WHERE
    clause, to catch a regression that drops the filter entirely.
    """

    repository, _mock_connection, mock_cursor = repository_with_mock_connection()
    record_a = mapping(employees=(employee_row(source_reference="source-A"),))
    record_b = mapping(employees=(employee_row(source_reference="source-B"),))

    outcome_a = repository.insert_mapping(record_a)
    outcome_b = repository.insert_mapping(record_b)
    replay_a = repository.insert_mapping(record_a)
    replay_b = repository.insert_mapping(record_b)

    for call in mock_cursor.execute.call_args_list:
        text = str(call.args[0])
        if "processing_audit" in text and "SELECT" in text.upper():
            assert "WHERE raw_event_ref = %s" in text

    assert outcome_a.inserted is True
    assert outcome_b.inserted is True
    assert replay_a.inserted is False
    assert replay_a.skipped_reason == "already_processed"
    assert replay_b.inserted is False
    assert replay_b.skipped_reason == "already_processed"


def test_processing_audit_insert_failure_rolls_back_and_next_component_still_succeeds() -> None:
    """Simulates losing a race: the final processing_audit insert violates
    the proposed unique index after the employees insert already succeeded.
    """
    repository, mock_connection, mock_cursor = repository_with_mock_connection()
    bad_record = mapping(employees=(employee_row(source_reference="source-race"),))
    good_record = mapping(employees=(employee_row(source_reference="source-ok"),))

    class FakeUniqueViolation(Exception):
        sqlstate = "23505"

    call_count = 0

    def execute_side_effect(query: object, params: object = None) -> None:
        nonlocal call_count
        call_count += 1
        text = str(query)
        # 3rd call overall is the bad component's processing_audit INSERT
        # (1: check, 2: employees insert, 3: audit insert).
        if call_count == 3 and "processing_audit" in text and "INSERT" in text.upper():
            raise FakeUniqueViolation("duplicate key value violates unique constraint")

    mock_cursor.execute.side_effect = execute_side_effect

    outcomes = repository.insert_mappings([bad_record, good_record])

    assert outcomes[0].inserted is False
    assert outcomes[0].skipped_reason == "insert_error"
    assert outcomes[1].inserted is True
    assert outcomes[1].employee_id == 42
    assert mock_connection.rollback.call_count == 1
    assert mock_connection.commit.call_count == 1  # only the good component commits


def test_already_processed_check_never_binds_a_business_identity_value() -> None:
    repository, _mock_connection, mock_cursor = repository_with_mock_connection()
    record = mapping(employees=(employee_row(passport="SHOULD-NOT-APPEAR-IN-CHECK"),))

    repository.insert_mapping(record)

    check_call = mock_cursor.execute.call_args_list[0]
    assert check_call.args[1] == ["p"]  # only the opaque source_reference is bound
    assert "SHOULD-NOT-APPEAR-IN-CHECK" not in check_call.args[1]
    assert "passport" not in str(check_call.args[0]).lower()


# ---------------------------------------------------------------------------
# HRP-57: enrich an already-processed component with genuinely new
# dependent data, without resolving person-identity or updating employees'
# own columns.
# ---------------------------------------------------------------------------


def test_enrichment_inserts_only_new_dependent_rows_for_existing_employee() -> None:
    repository, mock_connection, mock_cursor = repository_with_mock_connection()

    # First pass: only the Personal fragment, no dependents yet.
    first_outcome = repository.insert_mapping(mapping(employees=(employee_row(),)))
    assert first_outcome.inserted is True
    assert first_outcome.employee_id == 42

    # Second pass: same source_reference, now with a location that did not
    # exist before -- this is the incomplete -> complete case HRP-51 defines
    # at the transformation level.
    second_outcome = repository.insert_mapping(
        mapping(employees=(employee_row(),), locations=(location_row(),))
    )

    assert second_outcome.inserted is False
    assert second_outcome.employee_id == 42
    assert second_outcome.skipped_reason is None
    assert second_outcome.enriched_tables == ("locations",)

    # 1st pass: check + employees insert + audit insert (3 calls).
    # 2nd pass: check + find-existing-employee-id + dependent-exists check +
    # locations insert + audit-update insert (5 calls).
    assert mock_cursor.execute.call_count == 3 + 5
    # calls[0]=check, calls[1]=find-existing-employee-id, calls[2]=dependent
    # exists check (SELECT), calls[3]=locations INSERT, calls[4]=audit update.
    calls = mock_cursor.execute.call_args_list[3:]
    assert "SELECT employee_id FROM processing_audit" in _query_text(calls[1].args[0])
    assert '"locations"' in _query_text(calls[3].args[0])
    assert calls[3].args[1][0] == 42  # linked to the existing employee_id
    audit_update_call = calls[-1]
    audit_update_text = _query_text(audit_update_call.args[0])
    assert "UPDATE processing_audit" in audit_update_text
    assert "INSERT" not in audit_update_text.upper()  # updates the existing row, never a 2nd insert
    stage, status, employee_id, raw_event_ref = audit_update_call.args[1]
    assert stage == "update"
    assert status == "enriched"
    assert employee_id == 42
    assert raw_event_ref == "p"
    assert mock_connection.commit.call_count == 2


def test_reprocessing_with_no_new_dependent_data_writes_nothing() -> None:
    repository, mock_connection, mock_cursor = repository_with_mock_connection()

    first_outcome = repository.insert_mapping(
        mapping(employees=(employee_row(),), locations=(location_row(),))
    )
    assert first_outcome.inserted is True

    # Same source_reference, same exact location -- nothing new to add.
    second_outcome = repository.insert_mapping(
        mapping(employees=(employee_row(),), locations=(location_row(),))
    )

    assert second_outcome.inserted is False
    assert second_outcome.employee_id is None
    assert second_outcome.skipped_reason == "already_processed"
    assert second_outcome.enriched_tables == ()

    # No new employees/dependent/audit INSERT on the second pass: only the
    # check, the existing-employee lookup, and the dependent-exists check.
    calls_after_first_pass = mock_cursor.execute.call_args_list[4:]
    assert len(calls_after_first_pass) == 3
    for call in calls_after_first_pass:
        assert _query_text(call.args[0]).upper().startswith("SELECT")
    assert mock_connection.commit.call_count == 2  # first pass + second pass's read-only close


def test_enrichment_never_binds_a_business_identity_field() -> None:
    repository, _mock_connection, mock_cursor = repository_with_mock_connection()
    repository.insert_mapping(mapping(employees=(employee_row(passport="SHOULD-NOT-LEAK"),)))
    repository.insert_mapping(
        mapping(
            employees=(employee_row(passport="SHOULD-NOT-LEAK"),),
            locations=(location_row(),),
        )
    )

    lookup_call = mock_cursor.execute.call_args_list[4]  # 0-2: first pass, 3: check, 4: lookup
    assert "SELECT employee_id FROM processing_audit" in _query_text(lookup_call.args[0])
    assert lookup_call.args[1] == ["p"]  # only the opaque source_reference, never passport
    assert "SHOULD-NOT-LEAK" not in lookup_call.args[1]


def test_enrichment_does_not_touch_employees_own_columns() -> None:
    """No UPDATE statement against employees or any dependent table is ever
    issued -- the only UPDATE this module performs is HRP-57's own
    processing_audit bookkeeping row (see the comment on
    _record_processing_audit_update for why that one is an UPDATE, not a
    second INSERT: HRP-58's proposed unique index on raw_event_ref forbids
    it)."""
    repository, _mock_connection, mock_cursor = repository_with_mock_connection()
    repository.insert_mapping(mapping(employees=(employee_row(),)))
    repository.insert_mapping(mapping(employees=(employee_row(),), locations=(location_row(),)))

    update_calls = [
        call
        for call in mock_cursor.execute.call_args_list
        if _query_text(call.args[0]).upper().startswith("UPDATE")
    ]
    assert len(update_calls) == 1
    assert "UPDATE processing_audit" in _query_text(update_calls[0].args[0])


# ---------------------------------------------------------------------------
# HRP-57 review fixes: NULL-safe/full-column dependent equality, a locked
# existing-employee lookup to guard concurrent enrichment, and audit-update
# failure handling. The SQL-semantics claims themselves (NULL-safety, full
# equality across partial/complete inputs, actual concurrent blocking) are
# NOT provable by a Python-state mock -- see the real-database counterparts
# in tests/integration/test_person_repository.py, which is what actually
# proves them.
# ---------------------------------------------------------------------------


def test_existing_employee_lookup_locks_the_audit_row_for_update() -> None:
    """FOR UPDATE must be present in the SQL text: this is what prevents two
    concurrent enrichment attempts for the same source_reference from both
    seeing "not yet inserted" and duplicating a dependent row -- HRP-58's
    unique index on raw_event_ref does not protect this path."""
    repository, _mock_connection, mock_cursor = repository_with_mock_connection()
    repository.insert_mapping(mapping(employees=(employee_row(),)))
    repository.insert_mapping(mapping(employees=(employee_row(),), locations=(location_row(),)))

    lookup_calls = [
        call
        for call in mock_cursor.execute.call_args_list
        if "SELECT employee_id FROM processing_audit" in _query_text(call.args[0])
    ]
    assert len(lookup_calls) == 1
    assert "FOR UPDATE" in _query_text(lookup_calls[0].args[0]).upper()


def test_audit_update_failure_after_dependent_insert_rolls_back_and_batch_continues() -> None:
    """Simulates the audit UPDATE itself failing after a new dependent row
    was already inserted in the same transaction: the whole enrichment must
    roll back, and a following component in the same batch must still
    succeed."""
    repository, mock_connection, mock_cursor = repository_with_mock_connection()

    repository.insert_mapping(mapping(employees=(employee_row(source_reference="ref-a"),)))
    good_record = mapping(employees=(employee_row(source_reference="ref-b"),))
    enrich_record = mapping(
        employees=(employee_row(source_reference="ref-a"),),
        locations=(location_row(),),
    )

    call_count = 0
    original_side_effect = mock_cursor.execute.side_effect

    def execute_side_effect(query: object, params: object = None) -> None:
        nonlocal call_count
        call_count += 1
        text = _query_text(query).upper()
        if text.startswith("UPDATE PROCESSING_AUDIT") and call_count >= 4:
            raise Exception("audit update failed")
        original_side_effect(query, params)  # type: ignore[misc]

    mock_cursor.execute.side_effect = execute_side_effect

    outcomes = repository.insert_mappings([enrich_record, good_record])

    assert outcomes[0].inserted is False
    assert outcomes[0].skipped_reason == "insert_error"
    assert outcomes[1].inserted is True
    assert mock_connection.rollback.call_count == 1
    assert mock_connection.commit.call_count == 2  # ref-a's initial insert + good_record
