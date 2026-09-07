import json
import signal
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from confluent_kafka import Consumer, KafkaError

from ..observability.metrics import (
    CONSUMED_MESSAGES_TOTAL,
    PROCESSING_DURATION_SECONDS,
    Histogram,
    MonotonicCounter,
)
from .config import KAFKA_CONFIG, KAFKA_TOPICS
from .error_handler import get_logger
from .mongo import MongoIngestionClient, PersistenceOutcome

logger = get_logger("consumer")

running = True
consumed_messages_counter = MonotonicCounter(CONSUMED_MESSAGES_TOTAL)
processing_duration_histogram = Histogram(PROCESSING_DURATION_SECONDS)


@dataclass
class _ProcessingResult:
    raw_event: tuple[str, dict[str, Any], int, int] | None = None
    invalid_event: tuple[str, int, int, bytes | None, str] | None = None
    outcome_message: Any | None = None


def _process_message(msg: Any) -> _ProcessingResult:
    topic = msg.topic()
    if topic is None:
        logger.warning("Kafka message missing topic")
        return _ProcessingResult()
    partition = msg.partition()
    offset = msg.offset()
    if partition is None or offset is None:
        logger.warning("Kafka message missing coordinate")
        return _ProcessingResult()

    value = msg.value()
    if value is None:
        return _ProcessingResult(
            invalid_event=(topic, partition, offset, None, "missing_value"),
            outcome_message=msg,
        )

    try:
        data = json.loads(value.decode("utf-8"))
    except UnicodeDecodeError:
        return _ProcessingResult(
            invalid_event=(topic, partition, offset, value, "invalid_utf8"),
            outcome_message=msg,
        )
    except json.JSONDecodeError:
        return _ProcessingResult(
            invalid_event=(topic, partition, offset, value, "invalid_json"),
            outcome_message=msg,
        )

    if not isinstance(data, dict):
        return _ProcessingResult(
            invalid_event=(topic, partition, offset, value, "non_object_json"),
            outcome_message=msg,
        )
    return _ProcessingResult(raw_event=(topic, data, partition, offset), outcome_message=msg)


def _durable_prefix_messages(messages: list[Any], outcomes: list[PersistenceOutcome]) -> list[Any]:
    by_coordinate = {
        (outcome.topic, outcome.partition, outcome.offset): outcome for outcome in outcomes
    }
    grouped: dict[tuple[str, int], list[Any]] = defaultdict(list)
    for message in messages:
        grouped[(message.topic(), message.partition())].append(message)

    commits: list[Any] = []
    for partition_messages in grouped.values():
        ordered = sorted(partition_messages, key=lambda message: message.offset())
        expected = ordered[0].offset()
        last_durable = None
        for message in ordered:
            if message.offset() != expected:
                break
            outcome = by_coordinate.get((message.topic(), message.partition(), message.offset()))
            if outcome is None or outcome.status not in {"inserted", "already_exists"}:
                break
            last_durable = message
            expected += 1
        if last_durable is not None:
            commits.append(last_durable)
    return commits


def _shutdown(sig: int, frame: object) -> None:
    global running
    logger.info("Shutdown signal received — stopping after current message")
    running = False


signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)


def _handle_kafka_error(msg: Any) -> None:
    error = msg.error()
    if error.code() == KafkaError._PARTITION_EOF:
        logger.debug(f"End of partition | {msg.topic()} [{msg.partition()}]")
    else:
        logger.error(f"Kafka error: {error}")


def run_consumer(
    message_counter: MonotonicCounter | None = None,
    processing_timer: Histogram | None = None,
) -> None:
    counter = message_counter or consumed_messages_counter
    timer = processing_timer or processing_duration_histogram
    mongo_client = MongoIngestionClient()
    mongo_client.connect()

    consumer = Consumer(KAFKA_CONFIG)
    consumer.subscribe(KAFKA_TOPICS)
    logger.info(f"Subscribed to topics: {KAFKA_TOPICS}")

    try:
        while running:
            try:
                messages = consumer.consume(num_messages=500, timeout=1.0)
                if not messages:
                    continue

                raw_events: list[tuple[str, dict[str, Any], int, int]] = []
                outcome_messages: list[Any] = []
                outcomes: list[PersistenceOutcome] = []
                for msg in messages:
                    if msg.error():
                        _handle_kafka_error(msg)
                        continue

                    counter.increment()

                    started = time.perf_counter()
                    try:
                        result = _process_message(msg)
                    finally:
                        timer.observe(time.perf_counter() - started)

                    if result.raw_event is not None:
                        raw_events.append(result.raw_event)
                    if result.invalid_event is not None:
                        outcomes.append(mongo_client.persist_invalid_event(*result.invalid_event))
                    if result.outcome_message is not None:
                        outcome_messages.append(result.outcome_message)

                if raw_events:
                    outcomes.extend(mongo_client.persist_batch(raw_events))
                for commit_message in _durable_prefix_messages(outcome_messages, outcomes):
                    consumer.commit(message=commit_message)

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                continue

    finally:
        mongo_client.close()
        consumer.close()
        logger.info("Consumer closed cleanly")
