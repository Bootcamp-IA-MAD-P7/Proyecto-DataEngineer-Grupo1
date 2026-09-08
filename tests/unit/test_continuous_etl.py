from __future__ import annotations

from collections import defaultdict
from typing import Any

from hr_pro_platform.storage.person_repository import InsertOutcome
from hr_pro_platform.transformation.fragment_contract import ClassifiedFragment
from hr_pro_platform.transformation.main import (
    collect_connected_fragments,
    correlation_identifiers,
    process_raw_document,
)


class MemoryStore:
    def __init__(self) -> None:
        self.values: dict[str, list[ClassifiedFragment]] = defaultdict(list)

    def store_fragment(self, component_identifier: str, fragment: ClassifiedFragment) -> bool:
        if fragment in self.values[component_identifier]:
            return False
        self.values[component_identifier].append(fragment)
        return True

    def retrieve_fragments(self, component_identifier: str) -> tuple[ClassifiedFragment, ...]:
        return tuple(self.values[component_identifier])


class RecordingRepository:
    def __init__(self) -> None:
        self.mappings: list[Any] = []

    def insert_mappings(self, mappings: list[Any]) -> list[InsertOutcome]:
        self.mappings.extend(mappings)
        return [
            InsertOutcome(inserted=True, employee_id=1, skipped_reason=None)
            if mapping.employees
            else InsertOutcome(
                inserted=False, employee_id=None, skipped_reason="no_personal_domain"
            )
            for mapping in mappings
        ]


def _document(offset: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {"topic": "demo", "partition": 0, "offset": offset, "payload": payload}


def test_identifiers_are_opaque_and_bridge_personal_edges() -> None:
    fragment = ClassifiedFragment(
        payload={
            "name": "Synthetic",
            "last_name": "Employee",
            "sex": ["X"],
            "telfnumber": "000",
            "passport": "DEMO-PASSPORT",
            "email": "demo@example.invalid",
        },
        classification="Personal",
        source_reference="demo:0:1",
    )
    identifiers = correlation_identifiers(fragment)
    assert len(identifiers) == 2
    assert all(len(identifier) == 64 for identifier in identifiers)
    assert all(
        "Synthetic" not in identifier and "PASSPORT" not in identifier for identifier in identifiers
    )


def test_out_of_order_fragments_reach_one_complete_mapping() -> None:
    store = MemoryStore()
    repository = RecordingRepository()
    documents = [
        _document(1, {"passport": "DEMO-PASSPORT", "IBAN": "DEMO-IBAN", "salary": "1"}),
        _document(2, {"address": "Demo Street", "IPv4": "192.0.2.1"}),
        _document(
            3,
            {
                "fullname": "Synthetic Employee",
                "company": "Demo Company",
                "company address": "Demo Office",
                "company_telfnumber": "000",
                "company_email": "company@example.invalid",
                "job": "Engineer",
            },
        ),
        _document(4, {"fullname": "Synthetic Employee", "city": "Demo", "address": "Demo Street"}),
        _document(
            5,
            {
                "name": "Synthetic",
                "last_name": "Employee",
                "sex": ["X"],
                "telfnumber": "000",
                "passport": "DEMO-PASSPORT",
                "email": "demo@example.invalid",
            },
        ),
    ]

    results = [process_raw_document(document, store, repository) for document in documents]
    assert all(result.status == "processed" for result in results)
    complete = [mapping for mapping in repository.mappings if mapping.status == "complete"]
    assert complete
    final = complete[-1]
    assert len(final.employees) == 1
    assert len(final.locations) == 1
    assert len(final.professional_profiles) == 1
    assert len(final.bank_accounts) == 1
    assert len(final.network_data) == 1


def test_connected_fragment_collection_follows_transitive_edges() -> None:
    store = MemoryStore()
    repository = RecordingRepository()
    location = _document(
        1, {"fullname": "Synthetic Employee", "city": "Demo", "address": "Demo Street"}
    )
    net = _document(2, {"address": "Demo Street", "IPv4": "192.0.2.1"})
    process_raw_document(location, store, repository)
    process_raw_document(net, store, repository)

    location_fragment = next(
        fragment
        for values in store.values.values()
        for fragment in values
        if fragment.classification == "Location"
    )
    connected = collect_connected_fragments(store, correlation_identifiers(location_fragment))
    assert {fragment.classification for fragment in connected} == {"Location", "Net"}
