from unittest.mock import MagicMock, patch

from pytest import approx

from hr_pro_platform.ingestion.mongo import MongoIngestionClient
from hr_pro_platform.observability.metrics import (
    PERSISTENCE_DURATION_SECONDS,
    Histogram,
)


def _client(timer: Histogram) -> MongoIngestionClient:
    client = MongoIngestionClient(persistence_timer=timer)
    client._collection = MagicMock()
    client._invalid_collection = MagicMock()
    client._collection.find_one.return_value = None
    client._invalid_collection.find_one.return_value = None
    return client


def test_hrp79_records_one_duration_for_each_persisted_event() -> None:
    timer = Histogram(PERSISTENCE_DURATION_SECONDS)
    client = _client(timer)

    with patch(
        "hr_pro_platform.ingestion.mongo.time.perf_counter", side_effect=[1.0, 1.25, 2.0, 2.5]
    ):
        outcomes = client.persist_batch(
            [
                ("synthetic-topic", {"event": 1}, 0, 1),
                ("synthetic-topic", {"event": 2}, 0, 2),
            ]
        )

    assert [outcome.status for outcome in outcomes] == ["inserted", "inserted"]
    assert timer.count == 2
    assert timer.total == 0.75
    assert client._collection.insert_one.call_count == 2


def test_hrp79_records_failed_attempt_without_changing_persistence_outcome() -> None:
    timer = Histogram(PERSISTENCE_DURATION_SECONDS)
    client = _client(timer)
    client._collection.insert_one.side_effect = RuntimeError("synthetic failure")

    with patch("hr_pro_platform.ingestion.mongo.time.perf_counter", side_effect=[3.0, 3.4]):
        outcome = client.persist_raw_event("synthetic-topic", {"event": 1}, 0, 1)

    assert outcome.status == "failed"
    assert timer.count == 1
    assert timer.total == approx(0.4)
    client._collection.insert_one.assert_called_once()


def test_hrp79_duplicate_attempt_is_timed_once_and_keeps_existing_semantics() -> None:
    timer = Histogram(PERSISTENCE_DURATION_SECONDS)
    client = _client(timer)
    client._collection.find_one.return_value = {"already": True}

    with patch("hr_pro_platform.ingestion.mongo.time.perf_counter", side_effect=[4.0, 4.2]):
        outcome = client.persist_raw_event("synthetic-topic", {"event": 1}, 0, 1)

    assert outcome.status == "already_exists"
    assert timer.count == 1
    assert timer.total == approx(0.2)
    client._collection.insert_one.assert_not_called()
