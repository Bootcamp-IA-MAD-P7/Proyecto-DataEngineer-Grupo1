"""Produce privacy-safe aggregate evidence from the authorised HRP-43 RAW sample."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from typing import Any

from pymongo import MongoClient

AUTHORIZED_URI = "mongodb://localhost:27017/hr_pro"
AUTHORIZED_DATABASE = "hr_pro"
AUTHORIZED_COLLECTION = "raw_events_hrp43_20260901"
CANDIDATES = ("passport", "fullname", "address")


def _equal(left: Any, right: Any) -> bool:
    """Compare values exactly, including non-hashable JSON values."""
    result = left == right
    return bool(result) if isinstance(result, bool) else False


def _value_index(values: list[dict[str, Any]], value: Any) -> dict[str, Any]:
    for entry in values:
        if _equal(entry["value"], value):
            return entry
    entry = {"value": value, "count": 0, "shape_counts": Counter()}
    values.append(entry)
    return entry


def analyze_documents(documents: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Return aggregate metrics without returning candidate values or payloads."""
    shape_counts: Counter[tuple[str, ...]] = Counter()
    candidate_values: dict[str, list[dict[str, Any]]] = defaultdict(list)
    presence: dict[str, Counter[str]] = {candidate: Counter() for candidate in CANDIDATES}
    sample_size = 0

    for document in documents:
        payload = document.get("payload")
        if not isinstance(payload, Mapping):
            shape_counts[()] += 1
            sample_size += 1
            continue
        shape = tuple(sorted(str(field) for field in payload))
        shape_counts[shape] += 1
        sample_size += 1
        for candidate in CANDIDATES:
            if candidate not in payload:
                presence[candidate]["missing"] += 1
                continue
            value = payload[candidate]
            presence[candidate]["present"] += 1
            if value is None:
                presence[candidate]["null"] += 1
            elif value == "":
                presence[candidate]["empty"] += 1
            entry = _value_index(candidate_values[candidate], value)
            entry["count"] += 1
            entry["shape_counts"][shape] += 1

    candidates: dict[str, Any] = {}
    for candidate in CANDIDATES:
        values = candidate_values[candidate]
        non_empty = [
            entry for entry in values if entry["value"] is not None and entry["value"] != ""
        ]
        repeated = [entry for entry in non_empty if entry["count"] > 1]
        cross_shape = [entry for entry in non_empty if len(entry["shape_counts"]) > 1]
        candidates[candidate] = {
            "presence": dict(presence[candidate]),
            "distinct_value_count": len(non_empty),
            "repeated_value_count": len(repeated),
            "repeated_occurrence_count": sum(entry["count"] for entry in repeated),
            "cross_shape_value_count": len(cross_shape),
            "cross_shape_event_pair_count": sum(
                left_count * right_count
                for entry in cross_shape
                for left_shape, left_count in entry["shape_counts"].items()
                for right_shape, right_count in entry["shape_counts"].items()
                if left_shape < right_shape
            ),
            "collision_count": None,
            "counterexample_count": None,
            "collision_limitation": (
                "Person identity is not observed; same-value observations cannot be "
                "classified as collisions or counterexamples."
            ),
        }

    return {
        "sample_size": sample_size,
        "payload_shapes": [
            {"fields": list(shape), "count": count} for shape, count in sorted(shape_counts.items())
        ],
        "candidates": candidates,
        "comparison": "exact raw equality; no normalization or hashing",
    }


def collect_authorized_documents() -> Iterable[Mapping[str, Any]]:
    """Read only the fixed, authorised HRP-43 collection."""
    client: MongoClient[Any] = MongoClient(AUTHORIZED_URI, serverSelectionTimeoutMS=5000)
    try:
        yield from client[AUTHORIZED_DATABASE][AUTHORIZED_COLLECTION].find(
            {}, {"_id": 0, "payload": 1}
        )
    finally:
        client.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(analyze_documents(collect_authorized_documents()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
