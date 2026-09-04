from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from bson.binary import Binary
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError, DuplicateKeyError

from .config import MONGODB_COLLECTION, MONGODB_DB, MONGODB_INVALID_COLLECTION, MONGODB_URI
from .error_handler import get_logger

logger = get_logger("mongo")

PersistenceStatus = Literal["inserted", "already_exists", "failed", "unresolved_conflict"]


@dataclass(frozen=True)
class PersistenceOutcome:
    topic: str
    partition: int
    offset: int
    status: PersistenceStatus


class MongoIngestionClient:
    def __init__(self) -> None:
        self._client: MongoClient[Any] | None = None
        self._collection: Collection[Any] | None = None
        self._invalid_collection: Collection[Any] | None = None

    def connect(self) -> None:
        self._client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        self._client.admin.command("ping")
        self._collection = self._client[MONGODB_DB][MONGODB_COLLECTION]
        self._invalid_collection = self._client[MONGODB_DB][MONGODB_INVALID_COLLECTION]

        self._collection.create_index(
            [("partition", 1), ("offset", 1), ("topic", 1)],
            unique=True,
            name="unique_kafka_message",
        )
        self._collection.create_index("topic", name="topic_lookup")
        self._invalid_collection.create_index(
            [("partition", 1), ("offset", 1), ("topic", 1)],
            unique=True,
            name="unique_kafka_message",
        )

        logger.info("Connected to MongoDB | db=%s col=%s", MONGODB_DB, MONGODB_COLLECTION)

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            logger.info("MongoDB connection closed")

    def insert_raw_event(
        self, topic: str, payload: dict[str, Any], partition: int, offset: int
    ) -> bool:
        return self.persist_raw_event(topic, payload, partition, offset).status in {
            "inserted",
            "already_exists",
        }

    def persist_raw_event(
        self, topic: str, payload: dict[str, Any], partition: int, offset: int
    ) -> PersistenceOutcome:
        document = {
            "payload": payload,
            "topic": topic,
            "partition": partition,
            "offset": offset,
            "received_at": datetime.now(UTC),
            "processing_status": "pending",
        }
        return self._persist(
            self._collection, self._invalid_collection, document, topic, partition, offset
        )

    def insert_invalid_event(
        self,
        topic: str,
        partition: int,
        offset: int,
        payload: bytes | None,
        reason: str,
    ) -> bool:
        return self.persist_invalid_event(topic, partition, offset, payload, reason).status in {
            "inserted",
            "already_exists",
        }

    def persist_invalid_event(
        self,
        topic: str,
        partition: int,
        offset: int,
        payload: bytes | None,
        reason: str,
    ) -> PersistenceOutcome:
        document = {
            "topic": topic,
            "partition": partition,
            "offset": offset,
            "received_at": datetime.now(UTC),
            "payload": None if payload is None else Binary(payload),
            "reason": reason,
            "processing_status": "invalid",
        }
        return self._persist(
            self._invalid_collection, self._collection, document, topic, partition, offset
        )

    @staticmethod
    def _persist(
        collection: Collection[Any] | None,
        opposite: Collection[Any] | None,
        document: dict[str, Any],
        topic: str,
        partition: int,
        offset: int,
    ) -> PersistenceOutcome:
        coordinate = {"topic": topic, "partition": partition, "offset": offset}
        if collection is None or opposite is None:
            return PersistenceOutcome(topic, partition, offset, "failed")
        try:
            if opposite.find_one(coordinate) is not None:
                logger.error("Unresolved persistence conflict")
                return PersistenceOutcome(topic, partition, offset, "unresolved_conflict")
            if collection.find_one(coordinate) is not None:
                return PersistenceOutcome(topic, partition, offset, "already_exists")
            collection.insert_one(document)
            return PersistenceOutcome(topic, partition, offset, "inserted")
        except DuplicateKeyError:
            return PersistenceOutcome(topic, partition, offset, "already_exists")
        except BulkWriteError as error:
            if all(item.get("code") == 11000 for item in error.details.get("writeErrors", [])):
                return PersistenceOutcome(topic, partition, offset, "already_exists")
            logger.error("MongoDB persistence failed")
            return PersistenceOutcome(topic, partition, offset, "failed")
        except Exception:
            logger.error("MongoDB persistence failed")
            return PersistenceOutcome(topic, partition, offset, "failed")

    def persist_batch(
        self, events: list[tuple[str, dict[str, Any], int, int]]
    ) -> list[PersistenceOutcome]:
        return [self.persist_raw_event(*event) for event in events]

    def insert_many_fragments(self, messages: list[tuple[str, dict[str, Any], Any]]) -> bool:
        docs = []
        for topic, data, msg in messages:
            doc = {
                "topic": topic,
                "data": data,
                "received_at": datetime.now(UTC),
                "partition": msg.partition(),
                "offset": msg.offset(),
                "valid": True,
            }
            docs.append(doc)

        if not docs:
            return True

        assert self._collection is not None

        try:
            result = self._collection.insert_many(docs, ordered=False)
            logger.info("Inserted %d documents", len(result.inserted_ids))
            return True
        except BulkWriteError as bwe:
            code_11000 = [e for e in bwe.details.get("writeErrors", []) if e["code"] == 11000]
            if code_11000:
                logger.info("Duplicate documents skipped: %d", len(code_11000))
            non_duplicate = [e for e in bwe.details.get("writeErrors", []) if e["code"] != 11000]
            if non_duplicate:
                logger.error(
                    "MongoDB bulk insert failed | operation=insert_many status=failed "
                    "error_type=non_duplicate_bulk_write_error error_count=%d",
                    len(non_duplicate),
                )
                return False
            return True
        except Exception as error:
            logger.error(
                "MongoDB insert failed | operation=insert_many status=failed error_type=%s",
                type(error).__name__,
            )
            return False
