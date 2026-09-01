import json
import signal
from collections import defaultdict
from typing import Any

from confluent_kafka import Consumer, KafkaError

from .config import KAFKA_CONFIG, KAFKA_TOPICS
from .error_handler import get_logger
from .mongo import MongoIngestionClient, PersistenceOutcome

logger = get_logger("consumer")

running = True


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


def run_consumer() -> None:
    mongo_client = MongoIngestionClient()
    mongo_client.connect()

    consumer = Consumer(KAFKA_CONFIG)
    consumer.subscribe(KAFKA_TOPICS)
    logger.info(f"Subscribed to topics: {KAFKA_TOPICS}")

    msg_count = 0

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

                    topic = msg.topic()
                    if topic is None:
                        logger.warning("Kafka message missing topic")
                        continue
                    partition = msg.partition()
                    offset = msg.offset()
                    if partition is None or offset is None:
                        logger.warning("Kafka message missing coordinate")
                        continue

                    value = msg.value()
                    if value is None:
                        outcomes.append(
                            mongo_client.persist_invalid_event(
                                topic, partition, offset, None, "missing_value"
                            )
                        )
                        outcome_messages.append(msg)
                        continue

                    try:
                        data = json.loads(value.decode("utf-8"))
                    except UnicodeDecodeError:
                        outcomes.append(
                            mongo_client.persist_invalid_event(
                                topic, partition, offset, value, "invalid_utf8"
                            )
                        )
                        outcome_messages.append(msg)
                        continue
                    except json.JSONDecodeError:
                        outcomes.append(
                            mongo_client.persist_invalid_event(
                                topic, partition, offset, value, "invalid_json"
                            )
                        )
                        outcome_messages.append(msg)
                        continue

                    if not isinstance(data, dict):
                        outcomes.append(
                            mongo_client.persist_invalid_event(
                                topic, partition, offset, value, "non_object_json"
                            )
                        )
                        outcome_messages.append(msg)
                        continue

                    raw_events.append((topic, data, partition, offset))
                    outcome_messages.append(msg)

                if raw_events:
                    outcomes.extend(mongo_client.persist_batch(raw_events))
                for commit_message in _durable_prefix_messages(outcome_messages, outcomes):
                    consumer.commit(message=commit_message)
                msg_count += len(raw_events)

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                continue

    finally:
        mongo_client.close()
        consumer.close()
        logger.info("Consumer closed cleanly")
