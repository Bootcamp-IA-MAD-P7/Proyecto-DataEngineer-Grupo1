from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pymongo.errors import BulkWriteError


@dataclass
class FakeKafkaError:
    value: int = 1

    def code(self) -> int:
        return self.value


PERSONAL_DATA_PAYLOAD = (
    b'{"name": "Ana", "last_name": "Garcia", "passport": "X123", '
    b'"email": "ana@test.com", "telfnumber": "600000000", "sex": ["F"]}'
)

BANK_DATA_PAYLOAD = b'{"passport": "X123", "IBAN": "ES12345678901234567890", "salary": "50000"}'


@dataclass
class FakeMessage:
    payload: bytes | None = PERSONAL_DATA_PAYLOAD
    kafka_error: FakeKafkaError | None = None
    _topic: str = "authorised-topic"
    _partition: int = 0
    _offset: int = 7

    def error(self) -> FakeKafkaError | None:
        return self.kafka_error

    def topic(self) -> str:
        return self._topic

    def partition(self) -> int:
        return self._partition

    def offset(self) -> int:
        return self._offset

    def value(self) -> bytes | None:
        return self.payload


@dataclass
class FakeConsumer:
    messages: list[FakeMessage | None] = field(default_factory=list)
    _closed: bool = False
    _subscriptions: list[list[str]] = field(default_factory=list)
    _commits: list[Any] = field(default_factory=list)
    _index: int = 0

    def subscribe(self, topics: list[str]) -> None:
        self._subscriptions.append(topics)

    def consume(self, num_messages: int = 1, timeout: float = 1.0) -> list[FakeMessage | None]:
        remaining = self.messages[self._index : self._index + num_messages]
        self._index += num_messages
        return remaining

    def commit(self, message: Any = None, asynchronous: bool = False) -> None:
        self._commits.append(message)

    def close(self) -> None:
        self._closed = True


# ---------------------------------------------------------------------------
# consumer.py
# ---------------------------------------------------------------------------


@patch("hr_pro_platform.ingestion.consumer.MongoIngestionClient")
@patch("hr_pro_platform.ingestion.consumer.Consumer")
def test_consumer_processes_valid_messages(
    mock_kafka_cls: MagicMock, mock_mongo_cls: MagicMock
) -> None:
    fake_consumer = FakeConsumer(messages=[FakeMessage()])

    import hr_pro_platform.ingestion.consumer as consumer_mod

    original_consume = fake_consumer.consume

    def consume_once(*args: Any, **kwargs: Any) -> list[FakeMessage | None]:
        result = original_consume(*args, **kwargs)
        consumer_mod.running = False
        return result

    fake_consumer.consume = consume_once  # type: ignore[assignment]
    mock_kafka_cls.return_value = fake_consumer
    from hr_pro_platform.ingestion.mongo import PersistenceOutcome

    mock_mongo_cls.return_value.persist_batch.return_value = [
        PersistenceOutcome("authorised-topic", 0, 7, "inserted")
    ]

    consumer_mod.running = True
    consumer_mod.run_consumer()

    assert fake_consumer._closed is True
    mock_mongo_cls.return_value.persist_batch.assert_called_once()


@patch("hr_pro_platform.ingestion.consumer.MongoIngestionClient")
@patch("hr_pro_platform.ingestion.consumer.Consumer")
def test_consumer_skips_kafka_errors(mock_kafka_cls: MagicMock, mock_mongo_cls: MagicMock) -> None:
    fake_consumer = FakeConsumer(
        messages=[
            FakeMessage(kafka_error=FakeKafkaError()),
            FakeMessage(),
        ]
    )

    import hr_pro_platform.ingestion.consumer as consumer_mod

    original_consume = fake_consumer.consume

    def consume_once(*args: Any, **kwargs: Any) -> list[FakeMessage | None]:
        result = original_consume(*args, **kwargs)
        consumer_mod.running = False
        return result

    fake_consumer.consume = consume_once  # type: ignore[assignment]
    mock_kafka_cls.return_value = fake_consumer
    from hr_pro_platform.ingestion.mongo import PersistenceOutcome

    mock_mongo_cls.return_value.persist_invalid_event.return_value = PersistenceOutcome(
        "authorised-topic", 0, 7, "inserted"
    )

    consumer_mod.running = True
    consumer_mod.run_consumer()

    assert fake_consumer._closed is True


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        (None, "missing_value"),
        (b"{invalid", "invalid_json"),
        (b"[1, 2]", "non_object_json"),
        (b"\xff", "invalid_utf8"),
    ],
)
@patch("hr_pro_platform.ingestion.consumer.MongoIngestionClient")
@patch("hr_pro_platform.ingestion.consumer.Consumer")
def test_ac_05_routes_technical_invalid_values(
    mock_kafka_cls: MagicMock,
    mock_mongo_cls: MagicMock,
    payload: bytes | None,
    reason: str,
) -> None:
    fake_consumer = FakeConsumer(messages=[FakeMessage(payload=payload)])
    import hr_pro_platform.ingestion.consumer as consumer_mod

    original_consume = fake_consumer.consume

    def consume_once(*args: Any, **kwargs: Any) -> list[FakeMessage | None]:
        result = original_consume(*args, **kwargs)
        consumer_mod.running = False
        return result

    fake_consumer.consume = consume_once  # type: ignore[assignment]
    mock_kafka_cls.return_value = fake_consumer
    from hr_pro_platform.ingestion.mongo import PersistenceOutcome

    mock_mongo_cls.return_value.persist_batch.return_value = [
        PersistenceOutcome("authorised-topic", 0, 7, "inserted")
    ]
    consumer_mod.running = True
    consumer_mod.run_consumer()

    mock_mongo_cls.return_value.persist_invalid_event.assert_called_once_with(
        "authorised-topic", 0, 7, payload, reason
    )


@patch("hr_pro_platform.ingestion.consumer.MongoIngestionClient")
@patch("hr_pro_platform.ingestion.consumer.Consumer")
def test_ac_02_ac_03_ac_04_persist_json_object_without_business_classification(
    mock_kafka_cls: MagicMock, mock_mongo_cls: MagicMock
) -> None:
    payload = b'{"unknown": true}'
    fake_consumer = FakeConsumer(messages=[FakeMessage(payload=payload)])
    import hr_pro_platform.ingestion.consumer as consumer_mod

    original_consume = fake_consumer.consume

    def consume_once(*args: Any, **kwargs: Any) -> list[FakeMessage | None]:
        result = original_consume(*args, **kwargs)
        consumer_mod.running = False
        return result

    fake_consumer.consume = consume_once  # type: ignore[assignment]
    mock_kafka_cls.return_value = fake_consumer
    consumer_mod.running = True
    consumer_mod.run_consumer()

    mock_mongo_cls.return_value.persist_batch.assert_called_once_with(
        [("authorised-topic", {"unknown": True}, 0, 7)]
    )
    mock_mongo_cls.return_value.persist_invalid_event.assert_not_called()


# ---------------------------------------------------------------------------
# mongo.py — MongoIngestionClient
# ---------------------------------------------------------------------------


def _make_msg(topic: str = "t", partition: int = 0, offset: int = 0) -> MagicMock:
    msg = MagicMock()
    msg.topic.return_value = topic
    msg.partition.return_value = partition
    msg.offset.return_value = offset
    return msg


@patch("hr_pro_platform.ingestion.mongo.MongoClient")
def test_insert_many_returns_true_on_success(mock_cls: MagicMock) -> None:
    from hr_pro_platform.ingestion.mongo import MongoIngestionClient

    mock_collection = MagicMock()
    mock_collection.insert_many.return_value = MagicMock(inserted_ids=["id1"])

    client = MongoIngestionClient()
    client._collection = mock_collection

    result = client.insert_many_fragments([("personal-data", {"name": "Ana"}, _make_msg())])
    assert result is True
    mock_collection.insert_many.assert_called_once()


@patch("hr_pro_platform.ingestion.mongo.MongoClient")
def test_insert_many_returns_true_on_duplicate_key(mock_cls: MagicMock) -> None:
    from hr_pro_platform.ingestion.mongo import MongoIngestionClient

    mock_collection = MagicMock()
    bwe = BulkWriteError(
        {
            "writeErrors": [{"code": 11000, "errmsg": "duplicate"}],
            "nInserted": 0,
        }
    )
    mock_collection.insert_many.side_effect = bwe

    client = MongoIngestionClient()
    client._collection = mock_collection

    result = client.insert_many_fragments([("personal-data", {"name": "Ana"}, _make_msg())])
    assert result is True


@patch("hr_pro_platform.ingestion.mongo.MongoClient")
def test_insert_many_returns_false_on_unrecoverable_error(mock_cls: MagicMock) -> None:
    from hr_pro_platform.ingestion.mongo import MongoIngestionClient

    mock_collection = MagicMock()
    bwe = BulkWriteError(
        {
            "writeErrors": [{"code": 99999, "errmsg": "storage failure"}],
            "nInserted": 0,
        }
    )
    mock_collection.insert_many.side_effect = bwe

    client = MongoIngestionClient()
    client._collection = mock_collection

    result = client.insert_many_fragments([("personal-data", {"name": "Ana"}, _make_msg())])
    assert result is False


@patch("hr_pro_platform.ingestion.mongo.MongoClient")
def test_hrp67_bulk_write_error_log_excludes_raw_details_and_payload(
    mock_cls: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    from hr_pro_platform.ingestion.mongo import MongoIngestionClient

    sensitive_marker = "SYNTHETIC_SECRET_EMAIL_PASSPORT_IBAN"
    mock_collection = MagicMock()
    mock_collection.insert_many.side_effect = BulkWriteError(
        {
            "writeErrors": [
                {
                    "code": 99999,
                    "errmsg": f"storage failed for {sensitive_marker}",
                    "op": {"payload": {"email": sensitive_marker}},
                }
            ],
            "nInserted": 0,
        }
    )

    client = MongoIngestionClient()
    client._collection = mock_collection

    with caplog.at_level("ERROR"):
        result = client.insert_many_fragments(
            [("personal-data", {"email": sensitive_marker}, _make_msg())]
        )

    assert result is False
    assert "operation=insert_many" in caplog.text
    assert "status=failed" in caplog.text
    assert "error_type=non_duplicate_bulk_write_error" in caplog.text
    assert "error_count=1" in caplog.text
    assert sensitive_marker not in caplog.text
    assert "writeErrors" not in caplog.text
    assert "payload" not in caplog.text


@patch("hr_pro_platform.ingestion.mongo.MongoClient")
def test_hrp67_generic_insert_error_log_excludes_exception_message_and_traceback(
    mock_cls: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    from hr_pro_platform.ingestion.mongo import MongoIngestionClient

    sensitive_marker = "SYNTHETIC_SECRET_ADDRESS_PHONE"
    mock_collection = MagicMock()
    mock_collection.insert_many.side_effect = RuntimeError(
        f"database rejected sensitive value {sensitive_marker}"
    )

    client = MongoIngestionClient()
    client._collection = mock_collection

    with caplog.at_level("ERROR"):
        result = client.insert_many_fragments(
            [("personal-data", {"address": sensitive_marker}, _make_msg())]
        )

    assert result is False
    assert "operation=insert_many" in caplog.text
    assert "status=failed" in caplog.text
    assert "error_type=RuntimeError" in caplog.text
    assert sensitive_marker not in caplog.text
    assert "database rejected sensitive value" not in caplog.text
    assert all(record.exc_info is None for record in caplog.records)


def test_insert_many_returns_true_on_empty_list() -> None:
    from hr_pro_platform.ingestion.mongo import MongoIngestionClient

    client = MongoIngestionClient()
    result = client.insert_many_fragments([])
    assert result is True


@patch("hr_pro_platform.ingestion.mongo.MONGODB_COLLECTION", "test_col")
@patch("hr_pro_platform.ingestion.mongo.MONGODB_DB", "test_db")
@patch("hr_pro_platform.ingestion.mongo.MONGODB_URI", "mongodb://localhost:27017")
@patch("hr_pro_platform.ingestion.mongo.MongoClient")
def test_connect_calls_ping(mock_cls: MagicMock) -> None:
    from hr_pro_platform.ingestion.mongo import MongoIngestionClient

    mock_client = MagicMock()
    mock_cls.return_value = mock_client

    client = MongoIngestionClient()
    client.connect()

    mock_client.admin.command.assert_called_once_with("ping")


@patch("hr_pro_platform.ingestion.mongo.MONGODB_COLLECTION", "test_col")
@patch("hr_pro_platform.ingestion.mongo.MONGODB_DB", "test_db")
@patch("hr_pro_platform.ingestion.mongo.MONGODB_URI", "mongodb://localhost:27017")
@patch("hr_pro_platform.ingestion.mongo.MongoClient")
def test_connect_creates_indexes(mock_cls: MagicMock) -> None:
    from hr_pro_platform.ingestion.mongo import MongoIngestionClient

    mock_collection = MagicMock()
    mock_client = MagicMock()
    mock_client.__getitem__ = MagicMock(
        return_value=MagicMock(__getitem__=MagicMock(return_value=mock_collection))
    )
    mock_cls.return_value = mock_client

    client = MongoIngestionClient()
    client.connect()

    assert mock_collection.create_index.call_count == 3
    mock_collection.create_index.assert_any_call(
        [("partition", 1), ("offset", 1), ("topic", 1)],
        unique=True,
        name="unique_kafka_message",
    )
    mock_collection.create_index.assert_any_call("topic", name="topic_lookup")


@patch("hr_pro_platform.ingestion.mongo.MONGODB_COLLECTION", "test_col")
@patch("hr_pro_platform.ingestion.mongo.MONGODB_DB", "test_db")
@patch("hr_pro_platform.ingestion.mongo.MONGODB_URI", "mongodb://localhost:27017")
@patch("hr_pro_platform.ingestion.mongo.MongoClient")
def test_connect_raises_on_ping_failure(mock_cls: MagicMock) -> None:
    from hr_pro_platform.ingestion.mongo import MongoIngestionClient

    mock_client = MagicMock()
    mock_client.admin.command.side_effect = Exception("connection refused")
    mock_cls.return_value = mock_client

    client = MongoIngestionClient()
    with pytest.raises(Exception, match="connection refused"):
        client.connect()


@patch("hr_pro_platform.ingestion.mongo.MONGODB_COLLECTION", "test_col")
@patch("hr_pro_platform.ingestion.mongo.MONGODB_DB", "test_db")
@patch("hr_pro_platform.ingestion.mongo.MONGODB_URI", "mongodb://localhost:27017")
@patch("hr_pro_platform.ingestion.mongo.MongoClient")
def test_close_calls_client_close(mock_cls: MagicMock) -> None:
    from hr_pro_platform.ingestion.mongo import MongoIngestionClient

    mock_client = MagicMock()
    mock_cls.return_value = mock_client

    client = MongoIngestionClient()
    client._client = mock_client
    client.close()

    mock_client.close.assert_called_once()


def test_close_noop_when_not_connected() -> None:
    from hr_pro_platform.ingestion.mongo import MongoIngestionClient

    client = MongoIngestionClient()
    client.close()


def test_ac_06_raw_duplicate_returns_already_exists_without_second_insert() -> None:
    from hr_pro_platform.ingestion.mongo import MongoIngestionClient

    raw = MagicMock()
    invalid = MagicMock()
    raw.find_one.return_value = {"topic": "t"}
    invalid.find_one.return_value = None
    client = MongoIngestionClient()
    client._collection = raw
    client._invalid_collection = invalid

    outcome = client.persist_raw_event("t", {"synthetic": True}, 0, 1)

    assert outcome.status == "already_exists"
    raw.insert_one.assert_not_called()
    invalid.find_one.assert_called_once()


def test_ac_06_opposite_collection_returns_unresolved_conflict() -> None:
    from hr_pro_platform.ingestion.mongo import MongoIngestionClient

    raw = MagicMock()
    invalid = MagicMock()
    invalid.find_one.return_value = {"topic": "t"}
    client = MongoIngestionClient()
    client._collection = raw
    client._invalid_collection = invalid

    outcome = client.persist_raw_event("t", {"synthetic": True}, 0, 1)

    assert outcome.status == "unresolved_conflict"
    raw.insert_one.assert_not_called()


def test_ac_07_batch_returns_one_outcome_per_coordinate() -> None:
    from hr_pro_platform.ingestion.mongo import MongoIngestionClient

    raw = MagicMock()
    invalid = MagicMock()
    invalid.find_one.return_value = None
    raw.find_one.side_effect = [None, {"topic": "t"}]
    client = MongoIngestionClient()
    client._collection = raw
    client._invalid_collection = invalid

    outcomes = client.persist_batch([("t", {"synthetic": 1}, 0, 1), ("t", {"synthetic": 2}, 0, 2)])

    assert [outcome.status for outcome in outcomes] == ["inserted", "already_exists"]
    assert [(outcome.partition, outcome.offset) for outcome in outcomes] == [(0, 1), (0, 2)]


def test_ac_08_ac_10_commits_each_contiguous_partition_prefix() -> None:
    from hr_pro_platform.ingestion.consumer import _durable_prefix_messages
    from hr_pro_platform.ingestion.mongo import PersistenceOutcome

    messages = [
        FakeMessage(_offset=1),
        FakeMessage(_offset=2),
        FakeMessage(_partition=1, _offset=4),
    ]
    outcomes = [
        PersistenceOutcome("authorised-topic", 0, 1, "inserted"),
        PersistenceOutcome("authorised-topic", 0, 2, "already_exists"),
        PersistenceOutcome("authorised-topic", 1, 4, "inserted"),
    ]
    commits = _durable_prefix_messages(messages, outcomes)
    assert {(message.partition(), message.offset()) for message in commits} == {(0, 2), (1, 4)}


def test_ac_09_conflict_stops_prefix_without_commit() -> None:
    from hr_pro_platform.ingestion.consumer import _durable_prefix_messages
    from hr_pro_platform.ingestion.mongo import PersistenceOutcome

    messages = [FakeMessage(_offset=1), FakeMessage(_offset=2)]
    outcomes = [
        PersistenceOutcome("authorised-topic", 0, 1, "inserted"),
        PersistenceOutcome("authorised-topic", 0, 2, "unresolved_conflict"),
    ]
    commits = _durable_prefix_messages(messages, outcomes)
    assert [(message.partition(), message.offset()) for message in commits] == [(0, 1)]


def test_ac_11_conflict_log_contains_no_payload_or_operation(
    caplog: pytest.LogCaptureFixture,
) -> None:
    from hr_pro_platform.ingestion.mongo import MongoIngestionClient

    raw = MagicMock()
    invalid = MagicMock()
    raw.find_one.return_value = None
    invalid.find_one.return_value = {"topic": "t", "payload": "SYNTHETIC_SECRET"}
    client = MongoIngestionClient()
    client._collection = raw
    client._invalid_collection = invalid

    with caplog.at_level("ERROR"):
        client.persist_raw_event("t", {"payload": "SYNTHETIC_SECRET"}, 0, 1)

    assert "SYNTHETIC_SECRET" not in caplog.text
    assert "writeErrors" not in caplog.text


def test_ac_12_consumer_route_does_not_invoke_business_modules() -> None:
    from hr_pro_platform.ingestion import consumer

    assert "hr_pro_platform.ingestion.detector" not in consumer.__dict__
    assert "hr_pro_platform.ingestion.validator" not in consumer.__dict__


# ---------------------------------------------------------------------------
# main.py
# ---------------------------------------------------------------------------


@patch("hr_pro_platform.ingestion.main.run_consumer")
def test_main_calls_run_consumer(mock_run: MagicMock) -> None:
    from hr_pro_platform.ingestion.main import main

    main()
    mock_run.assert_called_once()


@patch("hr_pro_platform.ingestion.main.time.sleep")
@patch("hr_pro_platform.ingestion.main.run_consumer", side_effect=Exception("boom"))
def test_main_exits_after_max_retries(mock_run: MagicMock, mock_sleep: MagicMock) -> None:
    from hr_pro_platform.ingestion.main import main

    with pytest.raises(SystemExit, match="1"):
        main()
    assert mock_run.call_count == 5
