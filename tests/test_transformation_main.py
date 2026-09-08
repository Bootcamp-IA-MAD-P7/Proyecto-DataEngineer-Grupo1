from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from hr_pro_platform.storage.person_repository import InsertOutcome

MODULE = "hr_pro_platform.transformation.main"


@pytest.fixture()
def raw_documents() -> list[dict[str, Any]]:
    return [
        {
            "topic": "test-topic",
            "payload": {
                "name": "Alice",
                "last_name": "Smith",
                "sex": ["F"],
                "telfnumber": "555-0100",
                "passport": "T1234567",
                "email": "alice@test.com",
            },
            "partition": 0,
            "offset": 0,
        },
        {
            "topic": "test-topic",
            "payload": {
                "fullname": "Alice Smith",
                "city": "Testville",
                "address": "123 Test St",
            },
            "partition": 0,
            "offset": 1,
        },
        {
            "topic": "test-topic",
            "payload": {
                "fullname": "Alice Smith",
                "company": "TestCorp",
                "company address": "456 Corp Ave",
                "company_telfnumber": "555-0200",
                "company_email": "hr@testcorp.com",
                "job": "Engineer",
            },
            "partition": 0,
            "offset": 2,
        },
        {
            "topic": "test-topic",
            "payload": {
                "passport": "T1234567",
                "IBAN": "ES1234567890",
                "salary": "80000",
            },
            "partition": 0,
            "offset": 3,
        },
        {
            "topic": "test-topic",
            "payload": {"address": "123 Test St", "IPv4": "10.0.0.1"},
            "partition": 0,
            "offset": 4,
        },
    ]


def _make_insert_outcome(
    *,
    inserted: bool = True,
    employee_id: int | None = 1,
    skipped_reason: str | None = None,
) -> InsertOutcome:
    return InsertOutcome(
        inserted=inserted,
        employee_id=employee_id,
        skipped_reason=skipped_reason,
    )


@patch(f"{MODULE}.MongoIngestionClient")
@patch(f"{MODULE}.PersonRepository")
@patch(f"{MODULE}.PostgresSchemaClient")
def test_happy_path(
    mock_schema_class: MagicMock,
    mock_repo_class: MagicMock,
    mock_mongo_class: MagicMock,
    raw_documents: list[dict[str, Any]],
) -> None:
    mock_schema = mock_schema_class.return_value
    mock_repo = mock_repo_class.return_value
    mock_repo.insert_mappings.return_value = [
        _make_insert_outcome(inserted=True, employee_id=1),
    ]

    with patch(f"{MODULE}._read_all", return_value=raw_documents):
        from hr_pro_platform.transformation.main import main

        main()

    mock_schema.create_schema.assert_called_once()
    mock_repo.connect.assert_called_once()
    mock_repo.insert_mappings.assert_called_once()
    assert mock_repo.insert_mappings.call_args is not None
    mapping = mock_repo.insert_mappings.call_args[0][0][0]
    assert mapping.status == "complete"
    assert len(mapping.employees) == 1
    assert len(mapping.locations) == 1
    assert len(mapping.professional_profiles) == 1
    assert len(mapping.bank_accounts) == 1
    assert len(mapping.network_data) == 1
    mock_repo.close.assert_called_once()


@patch(f"{MODULE}.MongoIngestionClient")
@patch(f"{MODULE}.PersonRepository")
@patch(f"{MODULE}.PostgresSchemaClient")
def test_empty_batch(
    mock_schema_class: MagicMock,
    mock_repo_class: MagicMock,
    mock_mongo_class: MagicMock,
) -> None:
    with patch(f"{MODULE}._read_all", return_value=[]):
        from hr_pro_platform.transformation.main import main

        main()

    mock_repo_class.return_value.insert_mappings.assert_not_called()
    mock_repo_class.return_value.close.assert_called_once()


@patch(f"{MODULE}.MongoIngestionClient")
@patch(f"{MODULE}.PersonRepository")
@patch(f"{MODULE}.PostgresSchemaClient")
def test_idempotency_skips_already_processed(
    mock_schema_class: MagicMock,
    mock_repo_class: MagicMock,
    mock_mongo_class: MagicMock,
    raw_documents: list[dict[str, Any]],
) -> None:
    mock_repo = mock_repo_class.return_value
    mock_repo.insert_mappings.return_value = [
        _make_insert_outcome(inserted=True, employee_id=1),
        _make_insert_outcome(inserted=False, employee_id=None, skipped_reason="already_processed"),
    ]

    with patch(f"{MODULE}._read_all", return_value=raw_documents):
        from hr_pro_platform.transformation.main import main

        main()

    assert mock_repo.insert_mappings.call_count == 1
    results = mock_repo.insert_mappings.return_value
    inserted_count = sum(1 for r in results if r.inserted)
    skipped_count = sum(1 for r in results if not r.inserted and r.skipped_reason is not None)
    assert inserted_count == 1
    assert skipped_count == 1


@patch(f"{MODULE}.MongoIngestionClient")
@patch(f"{MODULE}.PersonRepository")
@patch(f"{MODULE}.PostgresSchemaClient")
def test_connection_error_is_caught(
    mock_schema_class: MagicMock,
    mock_repo_class: MagicMock,
    mock_mongo_class: MagicMock,
) -> None:
    mock_mongo = mock_mongo_class.return_value
    mock_mongo.connect.side_effect = ConnectionError("refused")

    from hr_pro_platform.transformation.main import main

    main()

    mock_repo_class.return_value.close.assert_called_once()


@patch(f"{MODULE}._classify_raw_documents")
@patch(f"{MODULE}.MongoIngestionClient")
@patch(f"{MODULE}.PersonRepository")
@patch(f"{MODULE}.PostgresSchemaClient")
def test_classification_error_aborts_batch(
    mock_schema_class: MagicMock,
    mock_repo_class: MagicMock,
    mock_mongo_class: MagicMock,
    mock_classify: MagicMock,
    raw_documents: list[dict[str, Any]],
) -> None:
    mock_classify.side_effect = RuntimeError("classification failure")

    with patch(f"{MODULE}._read_all", return_value=raw_documents):
        from hr_pro_platform.transformation.main import main

        main()

    mock_repo_class.return_value.insert_mappings.assert_not_called()
    mock_repo_class.return_value.close.assert_called_once()


@patch(f"{MODULE}._process_batch")
@patch(f"{MODULE}.MongoIngestionClient")
@patch(f"{MODULE}.PersonRepository")
@patch(f"{MODULE}.PostgresSchemaClient")
def test_batch_processing_error_retries(
    mock_schema_class: MagicMock,
    mock_repo_class: MagicMock,
    mock_mongo_class: MagicMock,
    mock_process: MagicMock,
    raw_documents: list[dict[str, Any]],
) -> None:
    mock_process.side_effect = RuntimeError("transient failure")

    with patch(f"{MODULE}._read_all", return_value=raw_documents):
        from hr_pro_platform.transformation.main import main

        main()

    assert mock_process.call_count == 5
    mock_repo_class.return_value.close.assert_called_once()


@patch(f"{MODULE}.MongoIngestionClient")
@patch(f"{MODULE}.PersonRepository")
@patch(f"{MODULE}.PostgresSchemaClient")
def test_multiple_batches(
    mock_schema_class: MagicMock,
    mock_repo_class: MagicMock,
    mock_mongo_class: MagicMock,
    raw_documents: list[dict[str, Any]],
) -> None:
    mock_repo = mock_repo_class.return_value
    mock_repo.insert_mappings.return_value = [
        _make_insert_outcome(inserted=True, employee_id=1),
    ]

    with patch(f"{MODULE}._read_all", return_value=raw_documents):
        with patch(f"{MODULE}.BATCH_SIZE", 3):
            from hr_pro_platform.transformation.main import main

            main()

    assert mock_repo.insert_mappings.call_count == 2


@patch(f"{MODULE}.MongoIngestionClient")
@patch(f"{MODULE}.PersonRepository")
@patch(f"{MODULE}.PostgresSchemaClient")
def test_main_returns_none(
    mock_schema_class: MagicMock,
    mock_repo_class: MagicMock,
    mock_mongo_class: MagicMock,
) -> None:
    with patch(f"{MODULE}._read_all", return_value=[]):
        from hr_pro_platform.transformation.main import main

        result = main()

    assert result is None
