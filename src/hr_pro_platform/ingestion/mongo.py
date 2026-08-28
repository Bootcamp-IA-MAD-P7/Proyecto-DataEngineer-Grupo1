from pymongo import MongoClient

from config import MONGO_URI, MONGO_DB, MONGO_COL
from detector import detect_topic
from error_handler import get_logger

logger = get_logger("mongo")

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = MongoClient(MONGO_URI)
        _collection = _client[MONGO_DB][MONGO_COL]
        logger.info(f"Connected to MongoDB | db={MONGO_DB} col={MONGO_COL}")
    return _collection


def insert_many_fragments(valid_batch: list[tuple[str, dict, object]]):
    col = _get_collection()
    docs = []
    for topic, data, msg in valid_batch:
        fragment_type = detect_topic(data)
        doc = {
            "payload": data,
            "fragment_type": fragment_type,
            "kafka_topic": msg.topic(),
            "kafka_partition": msg.partition(),
            "kafka_offset": msg.offset(),
        }
        docs.append(doc)
    if docs:
        col.insert_many(docs, ordered=False)
