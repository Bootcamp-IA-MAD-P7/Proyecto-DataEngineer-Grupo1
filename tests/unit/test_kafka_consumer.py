from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


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


@patch("hr_pro_platform.ingestion.consumer.MongoIngestionClient")
@patch("hr_pro_platform.ingestion.consumer.Consumer")
def test_consumer_processes_valid_messages(
    mock_kafka_cls: MagicMock, mock_mongo_cls: MagicMock
) -> None:
    fake_consumer = FakeConsumer(messages=[FakeMessage()])

    import hr_pro_platform.ingestion.consumer as consumer_mod

    original_consume = fake_consumer.consume
    call_count = 0

    def consume_once(*args: Any, **kwargs: Any) -> list[FakeMessage | None]:
        nonlocal call_count
        call_count += 1
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
    call_count = 0

    def consume_once(*args: Any, **kwargs: Any) -> list[FakeMessage | None]:
        nonlocal call_count
        call_count += 1
        result = original_consume(*args, **kwargs)
        consumer_mod.running = False
        return result

    fake_consumer.consume = consume_once  # type: ignore[assignment]
    mock_kafka_cls.return_value = fake_consumer

    consumer_mod.running = True
    consumer_mod.run_consumer()

    assert fake_consumer._closed is True
