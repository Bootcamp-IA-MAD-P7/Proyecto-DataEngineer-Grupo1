from __future__ import annotations

import pytest

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
