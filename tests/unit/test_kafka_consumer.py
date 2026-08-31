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
# config.py
# ---------------------------------------------------------------------------


def test_config_loads_mongodb_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "broker:9092")
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGODB_DB", "test_db")
    monkeypatch.setenv("MONGODB_COLLECTION", "test_col")

    from importlib import reload

    from hr_pro_platform.ingestion import config

    reload(config)

    assert config.MONGODB_URI == "mongodb://localhost:27017"
    assert config.MONGODB_DB == "test_db"
    assert config.MONGODB_COLLECTION == "test_col"


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

    consumer_mod.running = True
    consumer_mod.run_consumer()

    assert fake_consumer._closed is True
    mock_mongo_cls.return_value.insert_many_fragments.assert_called_once()


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

    consumer_mod.running = True
    consumer_mod.run_consumer()

    assert fake_consumer._closed is True


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

    assert mock_collection.create_index.call_count == 2
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
