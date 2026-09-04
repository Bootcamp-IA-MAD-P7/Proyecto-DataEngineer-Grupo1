"""Technical-only ETL logging helpers.

The functions in this module intentionally accept only bounded technical metadata.
They do not accept payloads, correlation values, secrets or personally identifiable
information.
"""

from __future__ import annotations

import json
import logging
from typing import Final

_EVENT_TYPE: Final = "etl_processing"
_COMPONENT: Final = "transformation"


def build_etl_log_event(
    *,
    stage: str,
    status: str,
    domain: str | None = None,
    input_count: int | None = None,
    output_count: int | None = None,
    unresolved_count: int | None = None,
    error_type: str | None = None,
    processing_time_ms: float | None = None,
) -> dict[str, str | int | float]:
    """Build a structured, non-sensitive ETL log event.

    Counts and timings are technical metadata. Payload values, Kafka keys,
    identifiers, addresses, emails, IBANs and other PII are deliberately outside this
    interface.
    """

    _require_text("stage", stage)
    _require_text("status", status)
    if domain is not None:
        _require_text("domain", domain)

    event: dict[str, str | int | float] = {
        "component": _COMPONENT,
        "event": _EVENT_TYPE,
        "stage": stage,
        "status": status,
    }
    _add_optional_text(event, "domain", domain)
    _add_optional_text(event, "error_type", error_type)
    _add_optional_count(event, "input_count", input_count)
    _add_optional_count(event, "output_count", output_count)
    _add_optional_count(event, "unresolved_count", unresolved_count)
    _add_optional_duration(event, processing_time_ms)
    return event


def log_etl_event(
    logger: logging.Logger,
    *,
    stage: str,
    status: str,
    domain: str | None = None,
    input_count: int | None = None,
    output_count: int | None = None,
    unresolved_count: int | None = None,
    error_type: str | None = None,
    processing_time_ms: float | None = None,
) -> None:
    """Emit one structured ETL event as JSON through the provided logger."""

    event = build_etl_log_event(
        stage=stage,
        status=status,
        domain=domain,
        input_count=input_count,
        output_count=output_count,
        unresolved_count=unresolved_count,
        error_type=error_type,
        processing_time_ms=processing_time_ms,
    )
    logger.info(json.dumps(event, ensure_ascii=True, sort_keys=True, separators=(",", ":")))


def _require_text(field: str, value: str) -> None:
    if value == "":
        raise ValueError(f"{field} must not be empty")


def _add_optional_text(
    event: dict[str, str | int | float],
    field: str,
    value: str | None,
) -> None:
    if value is not None:
        _require_text(field, value)
        event[field] = value


def _add_optional_count(
    event: dict[str, str | int | float],
    field: str,
    value: int | None,
) -> None:
    if value is not None:
        if value < 0:
            raise ValueError(f"{field} must be greater than or equal to 0")
        event[field] = value


def _add_optional_duration(
    event: dict[str, str | int | float],
    value: float | None,
) -> None:
    if value is not None:
        if value < 0:
            raise ValueError("processing_time_ms must be greater than or equal to 0")
        event["processing_time_ms"] = round(value, 3)


__all__: list[str] = ["build_etl_log_event", "log_etl_event"]
