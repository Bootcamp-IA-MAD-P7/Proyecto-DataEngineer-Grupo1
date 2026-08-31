import json
import signal
from typing import Any

from confluent_kafka import Consumer, KafkaError

from .config import KAFKA_CONFIG, KAFKA_TOPICS
from .detector import detect_topic
from .error_handler import get_logger
from .mongo import MongoIngestionClient
from .validator import validate

logger = get_logger("consumer")

running = True


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

                valid: list[tuple[str, dict[str, Any], Any]] = []
                for msg in messages:
                    if msg.error():
                        _handle_kafka_error(msg)
                        continue

                    topic = msg.topic()

                    value = msg.value()
                    if topic is None or value is None:
                        logger.warning(f"Empty message value | offset={msg.offset()}")
                        consumer.commit(message=msg)
                        continue

                    try:
                        data = json.loads(value.decode("utf-8"))
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        logger.warning(
                            f"Could not deserialise | topic={topic} offset={msg.offset()} | {e}"
                        )
                        consumer.commit(message=msg)
                        continue

                    detected_topic = detect_topic(data)
                    if detected_topic is None:
                        logger.warning(
                            "Could not detect fragment type | offset=%s", msg.offset()
                        )
                        consumer.commit(message=msg)
                        continue

                    if not validate(detected_topic, data):
                        logger.warning(
                            "Validation failed | topic=%s offset=%s", detected_topic, msg.offset()
                        )
                        consumer.commit(message=msg)
                        continue

                    valid.append((detected_topic, data, msg))

                if valid:
                    saved = mongo_client.insert_many_fragments(valid)
                    if saved:
                        consumer.commit(message=valid[-1][2])
                        logger.info(f"Batch saved | {len(valid)} messages")
                        msg_count += len(valid)
                        if msg_count >= 1000:
                            logger.info(f"Heartbeat | {msg_count} messages processed")
                            msg_count = 0
                    else:
                        logger.error("Batch insert failed — skipping commit, Kafka will redeliver")

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                continue

    finally:
        mongo_client.close()
        consumer.close()
        logger.info("Consumer closed cleanly")
