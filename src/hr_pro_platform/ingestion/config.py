import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DOTENV_PATH = Path(__file__).parent.parent.parent.parent / ".env"


def _load_environment(dotenv_path: Path = DOTENV_PATH) -> None:
    load_dotenv(dotenv_path, override=False)


@dataclass(frozen=True)
class IngestionSettings:
    kafka_config: dict[str, str | bool]
    kafka_topics: list[str]
    mongodb_uri: str
    mongodb_db: str
    mongodb_collection: str
    mongodb_invalid_collection: str


def _require(environ: Mapping[str, str], var: str) -> str:
    value = environ.get(var)
    if value is None:
        raise OSError(f"Missing required environment variable: {var}")
    if not value.strip():
        raise OSError(f"Empty required environment variable: {var}")
    return value


def _parse_topics(value: str) -> list[str]:
    topics = [topic.strip() for topic in value.split(",") if topic.strip()]
    if not topics:
        raise OSError("KAFKA_TOPICS must contain at least one topic")
    return topics


def build_settings(environ: Mapping[str, str]) -> IngestionSettings:
    return IngestionSettings(
        kafka_config={
            "bootstrap.servers": _require(environ, "KAFKA_BOOTSTRAP_SERVERS"),
            "group.id": _require(environ, "KAFKA_CONSUMER_GROUP"),
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        },
        kafka_topics=_parse_topics(_require(environ, "KAFKA_TOPICS")),
        mongodb_uri=_require(environ, "MONGODB_URI"),
        mongodb_db=_require(environ, "MONGODB_DB"),
        mongodb_collection=_require(environ, "MONGODB_COLLECTION"),
        mongodb_invalid_collection=_require(environ, "MONGODB_INVALID_COLLECTION"),
    )


_load_environment()
SETTINGS = build_settings(os.environ)

KAFKA_CONFIG = SETTINGS.kafka_config
KAFKA_TOPICS = SETTINGS.kafka_topics
MONGODB_URI = SETTINGS.mongodb_uri
MONGODB_DB = SETTINGS.mongodb_db
MONGODB_COLLECTION = SETTINGS.mongodb_collection
MONGODB_INVALID_COLLECTION = SETTINGS.mongodb_invalid_collection
