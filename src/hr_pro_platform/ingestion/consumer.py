import json
import signal

from config import KAFKA_CONFIG, KAFKA_TOPICS
from confluent_kafka import Consumer, KafkaError
from error_handler import get_logger

logger = get_logger("consumer")

running = True


def _shutdown(sig, frame):
    global running
    logger.info("Shutdown signal received — stopping after current message")
    running = False


signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)


def _handle_kafka_error(msg):
    error = msg.error()
    if error.code() == KafkaError._PARTITION_EOF:
        logger.debug(f"End of partition | {msg.topic()} [{msg.partition()}]")
    else:
        logger.error(f"Kafka error: {error}")


def run_consumer():
    consumer = Consumer(KAFKA_CONFIG)
    consumer.subscribe(KAFKA_TOPICS)
    logger.info(f"Subscribed to topics: {KAFKA_TOPICS}")

    msg_count = 0

    try:
        while running:
            try:
                msg = consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    _handle_kafka_error(msg)
                    continue

                topic = msg.topic()

                try:
                    data = json.loads(msg.value().decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.warning(
                        f"Could not deserialise | topic={topic} offset={msg.offset()} | {e}"
                    )
                    consumer.commit(message=msg)
                    continue

                logger.info(f"Received | topic={topic} | offset={msg.offset()}")

                msg_count += 1
                if msg_count % 1000 == 0:
                    logger.info(f"Heartbeat | {msg_count} messages processed")

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                continue

    finally:
        consumer.close()
        logger.info("Consumer closed cleanly")
