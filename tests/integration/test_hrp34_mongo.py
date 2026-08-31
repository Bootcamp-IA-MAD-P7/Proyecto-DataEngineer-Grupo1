from __future__ import annotations

import pytest
from pymongo.errors import DuplicateKeyError

from hr_pro_platform.ingestion.mongo import MongoIngestionClient


@pytest.fixture
def mongo_client(monkeypatch: pytest.MonkeyPatch) -> MongoIngestionClient:
    if not pytest.importorskip("pymongo"):
        pytest.skip("pymongo no disponible")
    monkeypatch.setattr(
        "hr_pro_platform.ingestion.mongo.MONGODB_URI", "mongodb://localhost:27017/hr_pro"
    )
    monkeypatch.setattr("hr_pro_platform.ingestion.mongo.MONGODB_DB", "hrp34_synthetic")
    monkeypatch.setattr(
        "hr_pro_platform.ingestion.mongo.MONGODB_COLLECTION", "raw_events_synthetic"
    )
    monkeypatch.setattr(
        "hr_pro_platform.ingestion.mongo.MONGODB_INVALID_COLLECTION",
        "invalid_events_synthetic",
    )
    client = MongoIngestionClient()
    try:
        client.connect()
    except Exception as exc:
        pytest.skip(f"MongoDB real no disponible: {type(exc).__name__}")
    client._collection.delete_many({})  # type: ignore[union-attr]
    client._invalid_collection.delete_many({})  # type: ignore[union-attr]
    try:
        yield client
    finally:
        client._collection.delete_many({})  # type: ignore[union-attr]
        client._invalid_collection.delete_many({})  # type: ignore[union-attr]
        client.close()


def test_ac_13_real_mongo_raw_and_invalid_contract(mongo_client: MongoIngestionClient) -> None:
    assert (
        mongo_client.persist_raw_event("synthetic-topic", {"synthetic": True}, 0, 1).status
        == "inserted"
    )
    assert (
        mongo_client.persist_invalid_event("synthetic-topic", 0, 2, b"[", "invalid_json").status
        == "inserted"
    )


def test_ac_13_real_mongo_binary_null_replay_conflict_and_legacy_isolation(
    mongo_client: MongoIngestionClient,
) -> None:
    raw = mongo_client._collection
    invalid = mongo_client._invalid_collection
    assert raw is not None and invalid is not None

    legacy = mongo_client._client["hrp34_synthetic"]["legacy_events_synthetic"]  # type: ignore[index]
    legacy.insert_one({"sentinel": "synthetic-legacy"})
    before_legacy = list(legacy.find({}))

    invalid_payload = b"not-json"
    assert (
        mongo_client.persist_invalid_event("synthetic-topic", 0, 10, invalid_payload, "invalid_json").status
        == "inserted"
    )
    stored_invalid = invalid.find_one({"topic": "synthetic-topic", "partition": 0, "offset": 10})
    assert bytes(stored_invalid["payload"]) == invalid_payload  # type: ignore[index]

    assert (
        mongo_client.persist_invalid_event("synthetic-topic", 0, 11, None, "missing_value").status
        == "inserted"
    )
    stored_missing = invalid.find_one({"topic": "synthetic-topic", "partition": 0, "offset": 11})
    assert stored_missing["payload"] is None  # type: ignore[index]

    assert mongo_client.persist_raw_event("synthetic-topic", {"synthetic": 1}, 0, 12).status == "inserted"
    with pytest.raises(DuplicateKeyError):
        raw.insert_one(
            {
                "payload": {"synthetic": 1},
                "topic": "synthetic-topic",
                "partition": 0,
                "offset": 12,
                "received_at": stored_missing["received_at"],  # type: ignore[index]
                "processing_status": "pending",
            }
        )
    assert mongo_client.persist_raw_event("synthetic-topic", {"synthetic": 1}, 0, 12).status == "already_exists"
    assert raw.count_documents({"topic": "synthetic-topic", "partition": 0, "offset": 12}) == 1

    conflict = mongo_client.persist_raw_event("synthetic-topic", {"synthetic": 2}, 0, 10)
    assert conflict.status == "unresolved_conflict"
    assert raw.count_documents({"topic": "synthetic-topic", "partition": 0, "offset": 10}) == 0
    assert list(legacy.find({})) == before_legacy
