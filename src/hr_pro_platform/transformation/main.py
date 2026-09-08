"""Continuous RAW-to-curated worker for the HR Pro pipeline.

The ingestion service owns Kafka acknowledgement and durable RAW persistence.
This worker consumes only MongoDB documents marked ``pending``, keeps temporary
correlation state in Redis and writes curated records through PersonRepository.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol, cast

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection

from ..ingestion.error_handler import get_logger
from ..storage.person_mapper import PersonRecordMapping, map_person_record
from ..storage.person_repository import InsertOutcome, PersonRepository
from ..storage.postgres import PostgresSchemaClient
from ..storage.redis import RedisPartialStateStore
from .bank_grouper import group_bank_fragments
from .classifier import UNKNOWN, classify_payload
from .fragment_contract import ClassifiedFragment, JSONValue
from .location_grouper import group_location_fragments
from .net_grouper import group_net_fragments
from .person_consolidator import consolidate_person_records
from .personal_grouper import group_personal_fragments
from .professional_grouper import group_professional_fragments
from .validator import validate_fragment

logger = get_logger("etl")

DEFAULT_BATCH_SIZE = 250
DEFAULT_POLL_SECONDS = 1.0


class PartialStateStore(Protocol):
    def store_fragment(self, component_identifier: str, fragment: ClassifiedFragment) -> bool: ...

    def retrieve_fragments(self, component_identifier: str) -> tuple[ClassifiedFragment, ...]: ...


class MappingRepository(Protocol):
    def insert_mappings(self, mappings: list[PersonRecordMapping]) -> list[InsertOutcome]: ...


@dataclass(frozen=True)
class ProcessingResult:
    status: str
    classification: str
    mappings: int = 0
    inserted: int = 0
    enriched: int = 0


def _positive_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    if not raw.isdecimal() or int(raw) <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return int(raw)


def _non_negative_float(name: str, default: float) -> float:
    raw = os.getenv(name, str(default))
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a non-negative number") from exc
    if value < 0:
        raise ValueError(f"{name} must be a non-negative number")
    return value


def _opaque_identifier(kind: str, value: str) -> str:
    """Hash a correlation value so Redis keys never contain personal data."""

    material = f"{kind}\x00{value}".encode()
    return hashlib.sha256(material).hexdigest()


def correlation_identifiers(fragment: ClassifiedFragment) -> tuple[str, ...]:
    """Return the opaque ADR-0006 exact-edge identifiers for one fragment."""

    if not isinstance(fragment.payload, Mapping):
        return ()
    payload = cast(Mapping[str, JSONValue], fragment.payload)
    candidates: list[tuple[str, object]] = []
    if fragment.classification == "Personal":
        candidates.append(("passport", payload.get("passport")))
        name = payload.get("name")
        last_name = payload.get("last_name")
        if isinstance(name, str) and isinstance(last_name, str):
            candidates.append(("fullname", f"{name} {last_name}"))
    elif fragment.classification == "Bank":
        candidates.append(("passport", payload.get("passport")))
    elif fragment.classification == "Location":
        candidates.extend(
            (("fullname", payload.get("fullname")), ("address", payload.get("address")))
        )
    elif fragment.classification == "Professional":
        candidates.append(("fullname", payload.get("fullname")))
    elif fragment.classification == "Net":
        candidates.append(("address", payload.get("address")))

    return tuple(
        sorted(
            {
                _opaque_identifier(kind, value)
                for kind, value in candidates
                if isinstance(value, str) and value != ""
            }
        )
    )


def _fragment_key(fragment: ClassifiedFragment) -> tuple[str, str, str]:
    return (
        fragment.classification,
        fragment.source_reference,
        json.dumps(fragment.payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")),
    )


def collect_connected_fragments(
    store: PartialStateStore, seed_identifiers: tuple[str, ...]
) -> list[ClassifiedFragment]:
    """Traverse Redis correlation buckets until their exact-edge closure is reached."""

    pending = list(seed_identifiers)
    visited: set[str] = set()
    fragments: dict[tuple[str, str, str], ClassifiedFragment] = {}
    while pending:
        identifier = pending.pop()
        if identifier in visited:
            continue
        visited.add(identifier)
        for fragment in store.retrieve_fragments(identifier):
            fragments[_fragment_key(fragment)] = fragment
            for related in correlation_identifiers(fragment):
                if related not in visited:
                    pending.append(related)
    return [fragments[key] for key in sorted(fragments)]


def _to_mappings(fragments: list[ClassifiedFragment]) -> list[PersonRecordMapping]:
    by_domain: dict[str, list[ClassifiedFragment]] = {
        "Personal": [],
        "Location": [],
        "Professional": [],
        "Bank": [],
        "Net": [],
    }
    for fragment in fragments:
        by_domain[fragment.classification].append(fragment)

    result = consolidate_person_records(
        group_personal_fragments(by_domain["Personal"]),
        group_location_fragments(by_domain["Location"]),
        group_professional_fragments(by_domain["Professional"]),
        group_bank_fragments(by_domain["Bank"]),
        group_net_fragments(by_domain["Net"]),
    )
    return [map_person_record(record) for record in result.records]


def process_raw_document(
    document: Mapping[str, Any], store: PartialStateStore, repository: MappingRepository
) -> ProcessingResult:
    """Classify one RAW event, update Redis state and persist its connected component."""

    payload = document.get("payload")
    if not isinstance(payload, Mapping):
        return ProcessingResult("unsupported", UNKNOWN)
    classification = classify_payload(payload)
    validation = validate_fragment(payload, classification)
    if not validation.is_valid or validation.payload is None:
        return ProcessingResult("unsupported", classification)

    source_reference = (
        f"{document.get('topic')}:{document.get('partition')}:{document.get('offset')}"
    )
    json_payload = cast(dict[str, JSONValue], dict(validation.payload))
    fragment = ClassifiedFragment(
        payload=json_payload,
        classification=classification,
        source_reference=source_reference,
    )
    identifiers = correlation_identifiers(fragment)
    if not identifiers:
        return ProcessingResult("uncorrelated", classification)

    for identifier in identifiers:
        store.store_fragment(identifier, fragment)
    connected = collect_connected_fragments(store, identifiers)
    mappings = _to_mappings(connected)
    outcomes = repository.insert_mappings(mappings)
    inserted = sum(outcome.inserted for outcome in outcomes)
    enriched = sum(bool(outcome.enriched_tables) for outcome in outcomes)
    if any(outcome.skipped_reason == "insert_error" for outcome in outcomes):
        return ProcessingResult("persistence_error", classification, len(mappings))
    return ProcessingResult("processed", classification, len(mappings), inserted, enriched)


def _ensure_schema() -> None:
    client = PostgresSchemaClient()
    client.connect()
    try:
        client.create_schema()
    finally:
        client.close()


def _raw_collection() -> tuple[MongoClient[Any], Collection[Any]]:
    uri = os.getenv("MONGODB_URI", "mongodb://mongo:27017/hr_pro")
    database = os.getenv("MONGODB_DB", "hr_pro")
    collection_name = os.getenv("MONGODB_COLLECTION", "raw_events")
    client: MongoClient[Any] = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    collection = client[database][collection_name]
    collection.create_index(
        [("processing_status", ASCENDING), ("received_at", ASCENDING)],
        name="etl_pending_received",
    )
    return client, collection


def _pending_batch(collection: Collection[Any], batch_size: int) -> list[dict[str, Any]]:
    return list(
        collection.find(
            {"processing_status": "pending"},
            {"payload": 1, "topic": 1, "partition": 1, "offset": 1},
        )
        .sort([("received_at", ASCENDING), ("_id", ASCENDING)])
        .limit(batch_size)
    )


def main() -> None:
    """Run the continuous MongoDB -> Redis -> PostgreSQL processing loop."""

    batch_size = _positive_int("HRP_ETL_BATCH_SIZE", DEFAULT_BATCH_SIZE)
    poll_seconds = _non_negative_float("HRP_ETL_POLL_SECONDS", DEFAULT_POLL_SECONDS)
    _ensure_schema()
    mongo_client, collection = _raw_collection()
    store = RedisPartialStateStore()
    repository = PersonRepository()
    store.connect()
    repository.connect()
    logger.info("Starting continuous ETL worker | batch_size=%d", batch_size)

    try:
        while True:
            documents = _pending_batch(collection, batch_size)
            if not documents:
                time.sleep(poll_seconds)
                continue
            counters: dict[str, int] = {}
            inserted = 0
            enriched = 0
            for document in documents:
                try:
                    result = process_raw_document(document, store, repository)
                except Exception as error:
                    logger.error(
                        "RAW event processing failed | error_class=%s", type(error).__name__
                    )
                    collection.update_one(
                        {"_id": document["_id"]},
                        {
                            "$set": {
                                "processing_status": "processing_error",
                                "processed_at": datetime.now(UTC),
                            }
                        },
                    )
                    counters["processing_error"] = counters.get("processing_error", 0) + 1
                    continue

                collection.update_one(
                    {"_id": document["_id"]},
                    {
                        "$set": {
                            "processing_status": result.status,
                            "classification": result.classification,
                            "processed_at": datetime.now(UTC),
                        }
                    },
                )
                counters[result.status] = counters.get(result.status, 0) + 1
                inserted += result.inserted
                enriched += result.enriched
            logger.info(
                "ETL batch completed | raw=%d processed=%d inserted=%d enriched=%d errors=%d",
                len(documents),
                counters.get("processed", 0),
                inserted,
                enriched,
                counters.get("processing_error", 0),
            )
    finally:
        repository.close()
        store.close()
        mongo_client.close()


if __name__ == "__main__":
    main()
