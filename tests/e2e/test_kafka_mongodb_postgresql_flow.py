"""HRP-71 E2E: Kafka-equivalent events -> MongoDB raw -> PostgreSQL curated.

The test uses synthetic Kafka coordinates and payloads. It does not start Kafka,
read the educational generator, or use real payload captures.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from typing import Any
from uuid import uuid4

import psycopg
import pytest


@pytest.fixture
def mongo_raw_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    kafka_import_defaults = {
        "KAFKA_BOOTSTRAP_SERVERS": "localhost:29092",
        "KAFKA_TOPICS": "synthetic-hrp71",
        "KAFKA_CONSUMER_GROUP": "hrp71-e2e",
    }
    for name, value in kafka_import_defaults.items():
        monkeypatch.setenv(name, value)

    from hr_pro_platform.ingestion.mongo import MongoIngestionClient

    monkeypatch.setattr(
        "hr_pro_platform.ingestion.mongo.MONGODB_URI", "mongodb://localhost:27017/hr_pro"
    )
    monkeypatch.setattr("hr_pro_platform.ingestion.mongo.MONGODB_DB", "hrp71_synthetic")
    monkeypatch.setattr("hr_pro_platform.ingestion.mongo.MONGODB_COLLECTION", "raw_events")
    monkeypatch.setattr(
        "hr_pro_platform.ingestion.mongo.MONGODB_INVALID_COLLECTION", "invalid_events"
    )

    client = MongoIngestionClient()
    try:
        client.connect()
    except Exception as exc:
        pytest.skip(f"MongoDB is not reachable for HRP-71 E2E: {type(exc).__name__}")

    assert client._collection is not None
    assert client._invalid_collection is not None
    client._collection.delete_many({})
    client._invalid_collection.delete_many({})
    try:
        yield client
    finally:
        client._collection.delete_many({})
        client._invalid_collection.delete_many({})
        client.close()


@pytest.fixture
def postgres_connection() -> Iterator[psycopg.Connection[tuple[object, ...]]]:
    try:
        import hr_pro_platform.storage.config as storage_config
    except OSError:
        pytest.skip("PostgreSQL environment variables are not configured.")

    try:
        connection = psycopg.connect(
            host=storage_config.POSTGRES_HOST,
            port=storage_config.POSTGRES_PORT,
            dbname=storage_config.POSTGRES_DB,
            user=storage_config.POSTGRES_USER,
            password=storage_config.POSTGRES_PASSWORD,
            connect_timeout=2,
        )
    except psycopg.OperationalError as exc:
        reason = str(exc).splitlines()[0]
        pytest.skip(
            "PostgreSQL is not reachable; "
            "start it with `docker compose -f infra/compose.dev.yml up -d postgres`. "
            f"Technical reason: {type(exc).__name__}: {reason}"
        )

    try:
        yield connection
    finally:
        connection.close()


def _synthetic_kafka_events(run_id: str) -> list[tuple[str, dict[str, Any], int, int]]:
    topic = f"synthetic-hrp71-{run_id}"
    partition = 0
    return [
        (
            topic,
            {
                "name": "Synthetic",
                "last_name": "Employee",
                "sex": ["X"],
                "telfnumber": "000-000-0000",
                "passport": "HRP71-PASSPORT",
                "email": "synthetic.employee@example.invalid",
            },
            partition,
            100,
        ),
        (
            topic,
            {
                "fullname": "Synthetic Employee",
                "city": "Synthetic City",
                "address": "71 Synthetic Street",
            },
            partition,
            101,
        ),
        (
            topic,
            {
                "fullname": "Synthetic Employee",
                "company": "Synthetic Company",
                "company address": "1 Synthetic Company Way",
                "company_telfnumber": "000-111-0000",
                "company_email": "company@example.invalid",
                "job": "Synthetic Engineer",
            },
            partition,
            102,
        ),
        (
            topic,
            {"passport": "HRP71-PASSPORT", "IBAN": "HRP71-IBAN", "salary": "71000"},
            partition,
            103,
        ),
        (
            topic,
            {"address": "71 Synthetic Street", "IPv4": "192.0.2.71"},
            partition,
            104,
        ),
    ]


def _fragments_from_raw_documents(raw_documents: Sequence[Mapping[str, Any]]) -> list[Any]:
    from hr_pro_platform.transformation.classifier import UNKNOWN, classify_payload
    from hr_pro_platform.transformation.fragment_contract import ClassifiedFragment
    from hr_pro_platform.transformation.validator import validate_fragment

    fragments: list[Any] = []
    for document in raw_documents:
        payload = document["payload"]
        assert isinstance(payload, Mapping)
        classification = classify_payload(payload)
        assert classification != UNKNOWN
        validation = validate_fragment(payload, classification)
        assert validation.is_valid is True
        fragments.append(
            ClassifiedFragment(
                payload=payload,
                classification=classification,
                source_reference=(
                    f"{document['topic']}:{document['partition']}:{document['offset']}"
                ),
            )
        )
    return fragments


def _run_transform_to_mapping(fragments: Sequence[Any]) -> list[Any]:
    from hr_pro_platform.storage.person_mapper import map_person_record
    from hr_pro_platform.transformation.bank_grouper import group_bank_fragments
    from hr_pro_platform.transformation.location_grouper import group_location_fragments
    from hr_pro_platform.transformation.net_grouper import group_net_fragments
    from hr_pro_platform.transformation.person_consolidator import consolidate_person_records
    from hr_pro_platform.transformation.personal_grouper import group_personal_fragments
    from hr_pro_platform.transformation.professional_grouper import group_professional_fragments

    by_domain: dict[str, list[Any]] = {
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


def _ensure_postgres_schema() -> None:
    from hr_pro_platform.storage.postgres import PostgresSchemaClient

    schema_client = PostgresSchemaClient()
    schema_client.connect()
    try:
        schema_client.create_schema()
    finally:
        schema_client.close()


def _cleanup_employee(
    connection: psycopg.Connection[tuple[object, ...]], employee_id: int | None
) -> None:
    if employee_id is None:
        return
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM processing_audit WHERE employee_id = %s", (employee_id,))
        cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
    connection.commit()


def test_kafka_equivalent_events_flow_from_mongodb_raw_to_postgresql_curated(
    mongo_raw_client: Any,
    postgres_connection: psycopg.Connection[tuple[object, ...]],
) -> None:
    from hr_pro_platform.storage.person_repository import PersonRepository

    _ensure_postgres_schema()

    run_id = uuid4().hex
    expected_topic = f"synthetic-hrp71-{run_id}"

    for event in _synthetic_kafka_events(run_id):
        outcome = mongo_raw_client.persist_raw_event(*event)
        assert outcome.status == "inserted"

    raw_collection = mongo_raw_client._collection
    assert raw_collection is not None
    raw_documents = list(raw_collection.find({}, sort=[("offset", 1)]))
    assert [(doc["topic"], doc["partition"], doc["offset"]) for doc in raw_documents] == [
        (expected_topic, 0, 100),
        (expected_topic, 0, 101),
        (expected_topic, 0, 102),
        (expected_topic, 0, 103),
        (expected_topic, 0, 104),
    ]

    mappings = _run_transform_to_mapping(_fragments_from_raw_documents(raw_documents))
    assert len(mappings) == 1
    mapping = mappings[0]
    assert mapping.status == "complete"

    repository = PersonRepository()
    repository.connect()
    employee_id: int | None = None
    try:
        outcome = repository.insert_mapping(mapping)
        assert outcome.inserted is True
        employee_id = outcome.employee_id
        assert employee_id is not None

        with postgres_connection.cursor() as cursor:
            cursor.execute(
                "SELECT first_name, last_name, passport FROM employees WHERE id = %s",
                (employee_id,),
            )
            employee_row = cursor.fetchone()
            cursor.execute(
                "SELECT city, address FROM locations WHERE employee_id = %s",
                (employee_id,),
            )
            location_rows = cursor.fetchall()
            cursor.execute(
                "SELECT company, job FROM professional_profiles WHERE employee_id = %s",
                (employee_id,),
            )
            professional_rows = cursor.fetchall()
            cursor.execute(
                "SELECT iban, salary FROM bank_accounts WHERE employee_id = %s",
                (employee_id,),
            )
            bank_rows = cursor.fetchall()
            cursor.execute(
                "SELECT ip_v4 FROM network_data WHERE employee_id = %s",
                (employee_id,),
            )
            net_rows = cursor.fetchall()

        assert employee_row == ("Synthetic", "Employee", "HRP71-PASSPORT")
        assert location_rows == [("Synthetic City", "71 Synthetic Street")]
        assert professional_rows == [("Synthetic Company", "Synthetic Engineer")]
        assert bank_rows == [("HRP71-IBAN", "71000")]
        assert net_rows == [("192.0.2.71",)]
    finally:
        _cleanup_employee(postgres_connection, employee_id)
        repository.close()
