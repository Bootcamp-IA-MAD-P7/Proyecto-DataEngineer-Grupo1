"""Kafka consumption with technical-only logging.

Payload interpretation and persistence belong to later tasks. This module records
only transport metadata and never logs a message body.
"""

from __future__ import annotations

import signal
from collections.abc import Callable
from typing import Any

from confluent_kafka import Consumer, KafkaError

from .config import KafkaConsumerSettings, load_kafka_settings
from .error_handler import get_logger

logger = get_logger(__name__)


class ShutdownController:
    """Keeps the polling loop testable while supporting graceful CLI shutdown."""

    def __init__(self) -> None:
        self.running = True

    def stop(self, _signal_number: int, _frame: object) -> None:
        logger.info("Shutdown signal received; stopping after the current poll")
        self.running = False

    def __call__(self) -> bool:
        return self.running


def install_signal_handlers(controller: ShutdownController) -> None:
    """Install process-level handlers only when the executable starts."""

    signal.signal(signal.SIGTERM, controller.stop)
    signal.signal(signal.SIGINT, controller.stop)


def _log_kafka_error(message: Any) -> None:
    error = message.error()
    if error.code() == KafkaError._PARTITION_EOF:
        logger.debug("End of partition topic=%s partition=%s", message.topic(), message.partition())
        return
    logger.warning("Kafka error type=%s", type(error).__name__)


def _log_message_metadata(message: Any) -> bool:
    value = message.value()
    if value is None:
        logger.warning(
            "Invalid Kafka message topic=%s partition=%s offset=%s reason=missing_value",
            message.topic(),
            message.partition(),
            message.offset(),
        )
        return False

    logger.info(
        "Kafka message received topic=%s partition=%s offset=%s bytes=%s",
        message.topic(),
        message.partition(),
        message.offset(),
        len(value),
    )
    return True


def run_consumer(
    settings: KafkaConsumerSettings | None = None,
    consumer_factory: Callable[[dict[str, object]], Any] = Consumer,
    should_continue: Callable[[], bool] | None = None,
    poll_timeout_seconds: float = 1.0,
    max_messages: int | None = None,
) -> int:
    """Consume authorised topics and return the number of valid transport events."""

    active_settings = settings or load_kafka_settings()
    consumer = consumer_factory(active_settings.client_config)
    keep_running = should_continue or (lambda: True)
    processed_messages = 0

    consumer.subscribe(list(active_settings.topics))
    logger.info("Kafka consumer subscribed topic_count=%s", len(active_settings.topics))

    try:
        while keep_running():
            try:
                message = consumer.poll(timeout=poll_timeout_seconds)
            except Exception as error:
                logger.error("Kafka poll failed error_type=%s", type(error).__name__)
                continue

            if message is None:
                continue
            if message.error():
                _log_kafka_error(message)
                continue
            if not _log_message_metadata(message):
                continue

            processed_messages += 1
            if max_messages is not None and processed_messages >= max_messages:
                break
    finally:
        consumer.close()
        logger.info("Kafka consumer closed processed_messages=%s", processed_messages)

    return processed_messages
