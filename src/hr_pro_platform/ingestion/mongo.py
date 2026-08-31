from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError

from .config import MONGODB_COLLECTION, MONGODB_DB, MONGODB_URI
from .error_handler import get_logger

logger = get_logger("mongo")


class MongoIngestionClient:
    def __init__(self) -> None:
        self._client: MongoClient[Any] | None = None
        self._collection: Collection[Any] | None = None

    def connect(self) -> None:
        self._client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        self._client.admin.command("ping")
        self._collection = self._client[MONGODB_DB][MONGODB_COLLECTION]

        self._collection.create_index(
            [("partition", 1), ("offset", 1), ("topic", 1)],
            unique=True,
            name="unique_kafka_message",
        )
        self._collection.create_index("topic", name="topic_lookup")

        logger.info("Connected to MongoDB | db=%s col=%s", MONGODB_DB, MONGODB_COLLECTION)

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            logger.info("MongoDB connection closed")

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
                logger.error("Non-duplicate write errors: %s", non_duplicate)
                return False
            return True
        except Exception:
            logger.error("Unrecoverable insert failure", exc_info=True)
            return False
