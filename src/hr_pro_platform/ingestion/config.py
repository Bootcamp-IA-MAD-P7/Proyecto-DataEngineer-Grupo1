"""Configuration for the Kafka consumer."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class KafkaConsumerSettings:
    """Runtime configuration for a consumer group."""

    bootstrap_servers: str
    consumer_group: str
    topics: tuple[str, ...]

    @property
    def client_config(self) -> dict[str, object]:
        return {
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": self.consumer_group,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _parse_topics(value: str) -> tuple[str, ...]:
    topics = tuple(topic.strip() for topic in value.split(",") if topic.strip())
    if not topics:
        raise ValueError("KAFKA_TOPICS must contain at least one authorised topic")
    return topics


def load_kafka_settings() -> KafkaConsumerSettings:
    """Load optional repository `.env` values without overriding the environment."""

    load_dotenv(_REPOSITORY_ROOT / ".env", override=False)
    return KafkaConsumerSettings(
        bootstrap_servers=_required("KAFKA_BOOTSTRAP_SERVERS"),
        consumer_group=_required("KAFKA_CONSUMER_GROUP"),
        topics=_parse_topics(_required("KAFKA_TOPICS")),
    )
