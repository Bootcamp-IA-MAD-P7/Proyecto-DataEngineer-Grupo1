from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock, patch


@dataclass
class ConsumerUnitFakeMessage:
    payload: bytes | None = b'{"synthetic": true}'
    kafka_error: object | None = None
    topic_name: str = "configured-topic"
    partition_id: int = 0
    offset_id: int = 1

    def error(self) -> object | None:
        return self.kafka_error

    def topic(self) -> str:
        return self.topic_name

    def partition(self) -> int:
        return self.partition_id

    def offset(self) -> int:
        return self.offset_id

    def value(self) -> bytes | None:
        return self.payload


@dataclass
class ConsumerUnitFakeConsumer:
    messages: list[ConsumerUnitFakeMessage] = field(default_factory=list)
    subscriptions: list[list[str]] = field(default_factory=list)
    commits: list[Any] = field(default_factory=list)
    closed: bool = False
    index: int = 0

    def subscribe(self, topics: list[str]) -> None:
        self.subscriptions.append(topics)

    def consume(self, num_messages: int = 1, timeout: float = 1.0) -> list[ConsumerUnitFakeMessage]:
        del timeout
        remaining = self.messages[self.index : self.index + num_messages]
        self.index += num_messages

        import hr_pro_platform.ingestion.consumer as consumer_mod

        consumer_mod.running = False
        return remaining

    def commit(self, message: Any = None, asynchronous: bool = False) -> None:
        del asynchronous
        self.commits.append(message)

    def close(self) -> None:
        self.closed = True


@patch("hr_pro_platform.ingestion.consumer.MongoIngestionClient")
@patch("hr_pro_platform.ingestion.consumer.Consumer")
def test_hrp68_subscribes_to_configured_topics_and_closes_clients(
    mock_consumer_class: MagicMock,
    mock_mongo_class: MagicMock,
) -> None:
    import hr_pro_platform.ingestion.consumer as consumer_mod
    from hr_pro_platform.ingestion.mongo import PersistenceOutcome

    message = ConsumerUnitFakeMessage()
    fake_consumer = ConsumerUnitFakeConsumer(messages=[message])
    mock_consumer_class.return_value = fake_consumer
    mock_mongo_class.return_value.persist_batch.return_value = [
        PersistenceOutcome("configured-topic", 0, 1, "inserted")
    ]

    original_topics = consumer_mod.KAFKA_TOPICS
    consumer_mod.KAFKA_TOPICS = ["configured-topic", "secondary-topic"]
    consumer_mod.running = True
    try:
        consumer_mod.run_consumer()
    finally:
        consumer_mod.KAFKA_TOPICS = original_topics
        consumer_mod.running = True

    assert fake_consumer.subscriptions == [["configured-topic", "secondary-topic"]]
    mock_mongo_class.return_value.connect.assert_called_once_with()
    mock_mongo_class.return_value.close.assert_called_once_with()
    assert fake_consumer.closed is True


@patch("hr_pro_platform.ingestion.consumer.MongoIngestionClient")
@patch("hr_pro_platform.ingestion.consumer.Consumer")
def test_hrp68_commits_valid_message_only_after_durable_persistence(
    mock_consumer_class: MagicMock,
    mock_mongo_class: MagicMock,
) -> None:
    import hr_pro_platform.ingestion.consumer as consumer_mod
    from hr_pro_platform.ingestion.mongo import PersistenceOutcome

    message = ConsumerUnitFakeMessage(offset_id=7)
    fake_consumer = ConsumerUnitFakeConsumer(messages=[message])
    mock_consumer_class.return_value = fake_consumer
    mock_mongo_class.return_value.persist_batch.return_value = [
        PersistenceOutcome("configured-topic", 0, 7, "already_exists")
    ]

    consumer_mod.running = True
    consumer_mod.run_consumer()
    consumer_mod.running = True

    mock_mongo_class.return_value.persist_batch.assert_called_once_with(
        [("configured-topic", {"synthetic": True}, 0, 7)]
    )
    assert fake_consumer.commits == [message]


@patch("hr_pro_platform.ingestion.consumer.MongoIngestionClient")
@patch("hr_pro_platform.ingestion.consumer.Consumer")
def test_hrp68_does_not_commit_when_raw_persistence_fails(
    mock_consumer_class: MagicMock,
    mock_mongo_class: MagicMock,
) -> None:
    import hr_pro_platform.ingestion.consumer as consumer_mod
    from hr_pro_platform.ingestion.mongo import PersistenceOutcome

    message = ConsumerUnitFakeMessage(offset_id=9)
    fake_consumer = ConsumerUnitFakeConsumer(messages=[message])
    mock_consumer_class.return_value = fake_consumer
    mock_mongo_class.return_value.persist_batch.return_value = [
        PersistenceOutcome("configured-topic", 0, 9, "failed")
    ]

    consumer_mod.running = True
    consumer_mod.run_consumer()
    consumer_mod.running = True

    assert fake_consumer.commits == []


@patch("hr_pro_platform.ingestion.consumer.MongoIngestionClient")
@patch("hr_pro_platform.ingestion.consumer.Consumer")
def test_hrp68_commits_invalid_payload_only_after_durable_invalid_persistence(
    mock_consumer_class: MagicMock,
    mock_mongo_class: MagicMock,
) -> None:
    import hr_pro_platform.ingestion.consumer as consumer_mod
    from hr_pro_platform.ingestion.mongo import PersistenceOutcome

    payload = b"{invalid"
    message = ConsumerUnitFakeMessage(payload=payload, offset_id=11)
    fake_consumer = ConsumerUnitFakeConsumer(messages=[message])
    mock_consumer_class.return_value = fake_consumer
    mock_mongo_class.return_value.persist_invalid_event.return_value = PersistenceOutcome(
        "configured-topic", 0, 11, "inserted"
    )

    consumer_mod.running = True
    consumer_mod.run_consumer()
    consumer_mod.running = True

    mock_mongo_class.return_value.persist_invalid_event.assert_called_once_with(
        "configured-topic", 0, 11, payload, "invalid_json"
    )
    mock_mongo_class.return_value.persist_batch.assert_not_called()
    assert fake_consumer.commits == [message]
