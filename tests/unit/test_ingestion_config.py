from __future__ import annotations

import os
from pathlib import Path

import pytest

from hr_pro_platform.ingestion import config

SYNTHETIC_ENV = {
    "KAFKA_BOOTSTRAP_SERVERS": "synthetic-broker.invalid:9092",
    "KAFKA_CONSUMER_GROUP": "synthetic-group",
    "KAFKA_TOPICS": "synthetic-topic-a,synthetic-topic-b",
    "MONGODB_URI": "mongodb://synthetic-mongo.invalid:27017/synthetic",
    "MONGODB_DB": "synthetic_db",
    "MONGODB_COLLECTION": "synthetic_raw_events",
    "MONGODB_INVALID_COLLECTION": "synthetic_invalid_events",
}


def _settings(
    *,
    overrides: dict[str, str] | None = None,
    missing: str | None = None,
) -> config.IngestionSettings:
    environ = SYNTHETIC_ENV | (overrides or {})
    if missing is not None:
        environ.pop(missing)
    return config.build_settings(environ)


def test_ac_01_loads_valid_configuration_from_environment() -> None:
    settings = _settings()

    assert settings.kafka_config["bootstrap.servers"] == "synthetic-broker.invalid:9092"
    assert settings.kafka_config["group.id"] == "synthetic-group"
    assert settings.kafka_topics == ["synthetic-topic-a", "synthetic-topic-b"]
    assert settings.mongodb_uri == "mongodb://synthetic-mongo.invalid:27017/synthetic"
    assert settings.mongodb_db == "synthetic_db"


@pytest.mark.parametrize("missing", tuple(SYNTHETIC_ENV))
def test_ac_01_rejects_missing_required_environment_variable(missing: str) -> None:
    with pytest.raises(OSError, match=rf"Missing required environment variable: {missing}"):
        _settings(missing=missing)


@pytest.mark.parametrize("blank", tuple(SYNTHETIC_ENV))
def test_ac_01_rejects_blank_required_environment_variable(blank: str) -> None:
    with pytest.raises(OSError, match=rf"Empty required environment variable: {blank}"):
        _settings(overrides={blank: "   "})


def test_ac_01_parses_comma_separated_topics() -> None:
    settings = _settings(
        overrides={"KAFKA_TOPICS": "synthetic-topic-a,synthetic-topic-b,synthetic-topic-c"}
    )

    assert settings.kafka_topics == [
        "synthetic-topic-a",
        "synthetic-topic-b",
        "synthetic-topic-c",
    ]


def test_ac_01_strips_topic_whitespace() -> None:
    settings = _settings(overrides={"KAFKA_TOPICS": " synthetic-topic-a ,  synthetic-topic-b  "})

    assert settings.kafka_topics == ["synthetic-topic-a", "synthetic-topic-b"]


def test_ac_01_rejects_empty_topic_list() -> None:
    with pytest.raises(OSError, match="KAFKA_TOPICS must contain at least one topic"):
        _settings(overrides={"KAFKA_TOPICS": " ,  , "})


def test_ac_01_process_environment_overrides_real_dotenv(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "KAFKA_BOOTSTRAP_SERVERS=dotenv-broker.invalid:9092\n"
        "KAFKA_TOPICS=dotenv-topic-a,dotenv-topic-b\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("PYTHON_DOTENV_DISABLED")
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "process-broker.invalid:9092")
    monkeypatch.delenv("KAFKA_TOPICS")

    config._load_environment(dotenv_path)

    assert os.environ["KAFKA_BOOTSTRAP_SERVERS"] == "process-broker.invalid:9092"
    assert os.environ["KAFKA_TOPICS"] == "dotenv-topic-a,dotenv-topic-b"


def test_ac_01_exposes_separate_raw_and_invalid_collections() -> None:
    settings = _settings()

    assert settings.mongodb_collection == "synthetic_raw_events"
    assert settings.mongodb_invalid_collection == "synthetic_invalid_events"


def test_ac_01_consumer_imports_with_public_configuration_constants() -> None:
    from hr_pro_platform.ingestion import consumer

    assert consumer.KAFKA_CONFIG is config.KAFKA_CONFIG
    assert consumer.KAFKA_TOPICS is config.KAFKA_TOPICS
    assert config.MONGODB_URI
    assert config.MONGODB_DB
    assert config.MONGODB_COLLECTION
    assert config.MONGODB_INVALID_COLLECTION
