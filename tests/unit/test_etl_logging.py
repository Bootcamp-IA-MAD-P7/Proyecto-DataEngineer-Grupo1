"""Tests for HRP-66 technical-only ETL logging."""

import json
import logging

import pytest

from hr_pro_platform.observability.etl_logging import build_etl_log_event, log_etl_event


def test_hrp66_builds_safe_structured_etl_event() -> None:
    event = build_etl_log_event(
        stage="classification",
        status="completed",
        domain="Personal",
        input_count=10,
        output_count=9,
        unresolved_count=1,
        processing_time_ms=12.34567,
    )

    assert event == {
        "component": "transformation",
        "domain": "Personal",
        "event": "etl_processing",
        "input_count": 10,
        "output_count": 9,
        "processing_time_ms": 12.346,
        "stage": "classification",
        "status": "completed",
        "unresolved_count": 1,
    }


def test_hrp66_log_output_excludes_payload_and_pii_fields(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("tests.hrp66")

    with caplog.at_level(logging.INFO, logger=logger.name):
        log_etl_event(
            logger,
            stage="grouping",
            status="completed",
            domain="Bank",
            input_count=3,
            output_count=1,
            unresolved_count=0,
            processing_time_ms=4.0,
        )

    assert len(caplog.messages) == 1
    event = json.loads(caplog.messages[0])
    assert event["stage"] == "grouping"
    assert event["domain"] == "Bank"
    assert "payload" not in event
    assert "passport" not in event
    assert "IBAN" not in event
    assert "email" not in event
    assert "address" not in event
    assert "salary" not in event
    assert "IPv4" not in event
    assert "correlation_key" not in event


@pytest.mark.parametrize(
    ("kwargs", "expected_error"),
    [
        (
            {"stage": "person@example.test", "status": "completed"},
            "stage must be one of the allowed technical values",
        ),
        (
            {"stage": "validation", "status": "ES91-0000-0000-0000-0000"},
            "status must be one of the allowed technical values",
        ),
        (
            {"stage": "grouping", "status": "failed", "domain": "passport-12345"},
            "domain must be one of the allowed technical values",
        ),
        (
            {
                "stage": "etl",
                "status": "failed",
                "error_type": "address 192.0.2.10 leaked",
            },
            "error_type must be one of the allowed technical values",
        ),
        (
            {"stage": "custom_stage", "status": "completed"},
            "stage must be one of the allowed technical values",
        ),
    ],
)
def test_hrp66_rejects_sensitive_or_arbitrary_textual_metadata(
    kwargs: dict[str, object],
    expected_error: str,
) -> None:
    with pytest.raises(ValueError, match=expected_error):
        build_etl_log_event(**kwargs)


@pytest.mark.parametrize(
    ("kwargs", "expected_error"),
    [
        (
            {"stage": "", "status": "completed"},
            "stage must be one of the allowed technical values",
        ),
        (
            {"stage": "validation", "status": ""},
            "status must be one of the allowed technical values",
        ),
        (
            {"stage": "validation", "status": "failed", "input_count": -1},
            "input_count must be greater than or equal to 0",
        ),
        (
            {"stage": "validation", "status": "failed", "processing_time_ms": -0.1},
            "processing_time_ms must be greater than or equal to 0",
        ),
    ],
)
def test_hrp66_rejects_invalid_technical_metadata(
    kwargs: dict[str, str | int | float],
    expected_error: str,
) -> None:
    with pytest.raises(ValueError, match=expected_error):
        build_etl_log_event(**kwargs)
