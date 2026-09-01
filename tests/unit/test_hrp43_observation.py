from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


def load_observer() -> Any:
    script = Path("scripts/hrp43_observe.py")
    spec = importlib.util.spec_from_file_location("hrp43_observe", script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_observation_emits_aggregate_metrics_without_values_or_payloads() -> None:
    observer = load_observer()
    result = observer.analyze_documents(
        [
            {"payload": {"passport": "synthetic-passport", "fullname": "synthetic-name"}},
            {"payload": {"address": "synthetic-address"}},
        ]
    )

    output = str(result)
    assert "synthetic-passport" not in output
    assert "synthetic-name" not in output
    assert "synthetic-address" not in output
    assert "payload" not in result
    assert result["sample_size"] == 2


def test_observation_detects_repeats_and_cross_shape_matches() -> None:
    observer = load_observer()
    result = observer.analyze_documents(
        [
            {"payload": {"passport": "same", "fullname": "one"}},
            {"payload": {"passport": "same", "address": "two"}},
            {"payload": {"passport": "other"}},
        ]
    )

    passport = result["candidates"]["passport"]
    assert passport["distinct_value_count"] == 2
    assert passport["repeated_value_count"] == 1
    assert passport["repeated_occurrence_count"] == 2
    assert passport["cross_shape_value_count"] == 1


def test_observation_handles_missing_null_and_empty_values() -> None:
    observer = load_observer()
    result = observer.analyze_documents(
        [
            {"payload": {"passport": None}},
            {"payload": {"passport": ""}},
            {"payload": {"fullname": "present"}},
        ]
    )

    passport = result["candidates"]["passport"]
    assert passport["presence"] == {"present": 2, "null": 1, "empty": 1, "missing": 1}
    assert passport["distinct_value_count"] == 0
    assert result["candidates"]["address"]["presence"] == {"missing": 3}
