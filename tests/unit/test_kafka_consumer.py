from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass

import pytest

from hr_pro_platform.ingestion.config import KafkaConsumerSettings, load_kafka_settings
from hr_pro_platform.ingestion.consumer import run_consumer


@dataclass
class FakeKafkaError:
    value: int = 1

    def code(self) -> int:
        return self.value


@dataclass
class FakeMessage:
    payload: bytes | None = b"safe-test-message"
    kafka_error: FakeKafkaError | None = None

    def error(self) -> FakeKafkaError | None:
        return self.kafka_error

    def topic(self) -> str:
        return "authorised-topic"

    def partition(self) -> int:
        return 0

    def offset(self) -> int:
        return 7

    def value(self) -> bytes | None:
        return self.payload


class FakeConsumer:
    def __init__(self, messages: list[FakeMessage | None]) -> None:
        self.messages: Iterator[FakeMessage | None] = iter(messages)
        self.closed = False
        self.subscriptions: list[list[str]] = []

    def subscribe(self, topics: list[str]) -> None:
        self.subscriptions.append(topics)

    def poll(self, timeout: float) -> FakeMessage | None:
        del timeout
        return next(self.messages)

    def close(self) -> None:
        self.closed = True


def _settings() -> KafkaConsumerSettings:
    return KafkaConsumerSettings(
        bootstrap_servers="broker.example:9092",
        consumer_group="hrp-30-test",
        topics=("authorised-topic",),
    )


def test_load_settings_uses_authorised_environment_topics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "broker.example:9092")
    monkeypatch.setenv("KAFKA_CONSUMER_GROUP", "hrp-30-test")
    monkeypatch.setenv("KAFKA_TOPICS", "authorised-topic, another-topic")

    settings = load_kafka_settings()

    assert settings.topics == ("authorised-topic", "another-topic")


def test_load_settings_rejects_missing_topics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "broker.example:9092")
    monkeypatch.setenv("KAFKA_CONSUMER_GROUP", "hrp-30-test")
    monkeypatch.setenv("KAFKA_TOPICS", "")

    with pytest.raises(ValueError, match="KAFKA_TOPICS"):
        load_kafka_settings()


def test_consumer_counts_metadata_without_logging_payload() -> None:
    fake_consumer = FakeConsumer([FakeMessage()])

    processed = run_consumer(
        settings=_settings(),
        consumer_factory=lambda _config: fake_consumer,
        max_messages=1,
    )

    assert processed == 1
    assert fake_consumer.subscriptions == [["authorised-topic"]]
    assert fake_consumer.closed is True


def test_consumer_logs_technical_metadata_without_payload(caplog: pytest.LogCaptureFixture) -> None:
    payload_sentinel = b"must-not-appear-in-logs"
    fake_consumer = FakeConsumer([FakeMessage(payload=payload_sentinel)])

    with caplog.at_level(logging.INFO, logger="hr_pro_platform.ingestion.consumer"):
        processed = run_consumer(
            settings=_settings(),
            consumer_factory=lambda _config: fake_consumer,
            max_messages=1,
        )

    logged_output = caplog.text

    assert processed == 1
    assert "Kafka consumer subscribed topic_count=1" in logged_output
    assert (
        "Kafka message received topic=authorised-topic partition=0 offset=7 bytes=23"
        in logged_output
    )
    assert "Kafka consumer closed processed_messages=1" in logged_output
    assert payload_sentinel.decode() not in logged_output


def test_invalid_message_log_does_not_include_payload(caplog: pytest.LogCaptureFixture) -> None:
    payload_sentinel = b"must-not-appear-in-logs"
    fake_consumer = FakeConsumer([FakeMessage(payload=None), FakeMessage(payload=payload_sentinel)])

    with caplog.at_level(logging.WARNING, logger="hr_pro_platform.ingestion.consumer"):
        processed = run_consumer(
            settings=_settings(),
            consumer_factory=lambda _config: fake_consumer,
            max_messages=1,
        )

    assert processed == 1
    assert "reason=missing_value" in caplog.text
    assert payload_sentinel.decode() not in caplog.text


def test_consumer_skips_errors_and_invalid_messages() -> None:
    fake_consumer = FakeConsumer(
        [
            FakeMessage(kafka_error=FakeKafkaError()),
            FakeMessage(payload=None),
            FakeMessage(),
        ]
    )

    processed = run_consumer(
        settings=_settings(),
        consumer_factory=lambda _config: fake_consumer,
        max_messages=1,
    )

    assert processed == 1
    assert fake_consumer.closed is True
