"""ETL orchestration: MongoDB raw_events -> transformation -> PostgreSQL curated.

Extracts the exact flow from tests/e2e/test_kafka_mongodb_postgresql_flow.py
(_fragments_from_raw_documents + _run_transform_to_mapping) into a production
entrypoint. Idempotency is provided by PersonRepository.insert_mapping()
(HRP-58): processing_audit checks prevent duplicate inserts on re-runs.
"""

from __future__ import annotations

import time
from collections.abc import Iterator, Mapping
from typing import Any

from ..ingestion.error_handler import get_logger
from ..ingestion.mongo import MongoIngestionClient
from ..storage.person_mapper import map_person_record
from ..storage.person_repository import PersonRepository
from ..storage.postgres import PostgresSchemaClient
from .bank_grouper import group_bank_fragments
from .classifier import UNKNOWN, classify_payload
from .fragment_contract import ClassifiedFragment
from .location_grouper import group_location_fragments
from .net_grouper import group_net_fragments
from .person_consolidator import consolidate_person_records
from .personal_grouper import group_personal_fragments
from .professional_grouper import group_professional_fragments
from .validator import validate_fragment

logger = get_logger("etl")

BATCH_SIZE = 5000
MAX_RETRIES = 5
BASE_DELAY = 1


def _classify_raw_documents(
    raw_documents: list[dict[str, Any]],
) -> list[ClassifiedFragment]:
    """Classify raw Mongo documents into domain-specific fragments.

    Follows the exact logic of the e2e test helper
    ``_fragments_from_raw_documents``.
    """
    fragments: list[ClassifiedFragment] = []
    for document in raw_documents:
        payload: Mapping[str, object] = document["payload"]
        classification = classify_payload(payload)
        if classification == UNKNOWN:
            logger.warning(
                "Skipping unknown classification | source=%s:%s:%s",
                document.get("topic"),
                document.get("partition"),
                document.get("offset"),
            )
            continue
        validation = validate_fragment(payload, classification)
        if not validation.is_valid:
            logger.warning(
                "Skipping invalid fragment | source=%s:%s:%s",
                document.get("topic"),
                document.get("partition"),
                document.get("offset"),
            )
            continue
        source_ref = f"{document['topic']}:{document['partition']}:{document['offset']}"
        fragments.append(
            ClassifiedFragment(
                payload=payload,
                classification=classification,
                source_reference=source_ref,
            )
        )
    return fragments


def _transform_to_mappings(
    fragments: list[ClassifiedFragment],
) -> list[Any]:
    """Group, consolidate and map fragments into PersonRecordMappings.

    Follows the exact logic of the e2e test helper
    ``_run_transform_to_mapping``.
    """
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


def _read_all(mongo_client: MongoIngestionClient) -> list[dict[str, Any]]:
    """Read all raw_events from MongoDB sorted by offset."""
    assert mongo_client._collection is not None
    cursor: Iterator[dict[str, Any]] = mongo_client._collection.find({}, sort=[("offset", 1)])
    documents: list[dict[str, Any]] = []
    while True:
        try:
            documents.append(next(cursor))
        except StopIteration:
            break
    return documents


def _process_batch(
    raw_documents: list[dict[str, Any]],
    repository: PersonRepository,
) -> tuple[int, int]:
    """Transform and insert one batch. Returns (inserted, skipped) counts."""
    fragments = _classify_raw_documents(raw_documents)
    if not fragments:
        return 0, 0

    mappings = _transform_to_mappings(fragments)
    if not mappings:
        return 0, 0

    outcomes = repository.insert_mappings(mappings)
    inserted = sum(1 for o in outcomes if o.inserted)
    skipped = sum(1 for o in outcomes if not o.inserted and o.skipped_reason is not None)
    return inserted, skipped


def main() -> None:
    """Run the ETL pipeline: MongoDB raw_events -> PostgreSQL curated tables."""
    schema_client = PostgresSchemaClient()
    schema_client.connect()
    try:
        schema_client.create_schema()
    finally:
        schema_client.close()
    logger.info("PostgreSQL schema ensured")

    repository = PersonRepository()
    repository.connect()

    total_inserted = 0
    total_skipped = 0

    try:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(
                    "Starting ETL pipeline (attempt %d/%d)",
                    attempt,
                    MAX_RETRIES,
                )
                mongo_client = MongoIngestionClient()
                mongo_client.connect()

                raw_all = _read_all(mongo_client)
                if not raw_all:
                    logger.info("No raw events to process")
                    break

                batch_number = 0
                while batch_number * BATCH_SIZE < len(raw_all):
                    start = batch_number * BATCH_SIZE
                    raw_batch = raw_all[start : start + BATCH_SIZE]
                    inserted, skipped = _process_batch(raw_batch, repository)
                    total_inserted += inserted
                    total_skipped += skipped
                    logger.info(
                        "Batch %d processed | raw=%d inserted=%d skipped=%d",
                        batch_number,
                        len(raw_batch),
                        inserted,
                        skipped,
                    )
                    batch_number += 1

                logger.info(
                    "ETL complete | total_inserted=%d total_skipped=%d",
                    total_inserted,
                    total_skipped,
                )
                break
            except Exception as error:
                delay = BASE_DELAY * (2 ** (attempt - 1))
                logger.error("Fatal error on attempt %d: %s", attempt, error)
                if attempt == MAX_RETRIES:
                    logger.error("Max retries reached")
                    break
                logger.info("Retrying in %ds...", delay)
                time.sleep(delay)
    finally:
        repository.close()


if __name__ == "__main__":
    main()
