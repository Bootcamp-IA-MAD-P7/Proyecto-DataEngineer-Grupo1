"""Technical-only ETL logging helpers.

The functions in this module intentionally accept only bounded technical metadata.
They do not accept payloads, correlation values, secrets or personally identifiable
information.
"""

from __future__ import annotations

import json
import logging
import math
from typing import Final, Literal, TypeAlias

_EVENT_TYPE: Final = "etl_processing"
_COMPONENT: Final = "transformation"

ETLStage: TypeAlias = Literal["classification", "validation", "grouping", "consolidation", "etl"]
ETLStatus: TypeAlias = Literal["started", "completed", "failed", "skipped"]
ETLDomain: TypeAlias = Literal["Personal", "Location", "Professional", "Bank", "Net", "unknown"]
ETLErrorType: TypeAlias = Literal[
    "invalid_metadata",
    "validation_error",
    "classification_error",
    "grouping_error",
    "consolidation_error",
    "unexpected_error",
]

_ALLOWED_STAGES: Final[frozenset[str]] = frozenset(
    {"classification", "validation", "grouping", "consolidation", "etl"}
)
_ALLOWED_STATUSES: Final[frozenset[str]] = frozenset({"started", "completed", "failed", "skipped"})
_ALLOWED_DOMAINS: Final[frozenset[str]] = frozenset(
    {"Personal", "Location", "Professional", "Bank", "Net", "unknown"}
)
_ALLOWED_ERROR_TYPES: Final[frozenset[str]] = frozenset(
    {
        "invalid_metadata",
        "validation_error",
        "classification_error",
        "grouping_error",
        "consolidation_error",
        "unexpected_error",
    }
)


def build_etl_log_event(
    *,
    stage: ETLStage,
    status: ETLStatus,
    domain: ETLDomain | None = None,
    input_count: int | None = None,
    output_count: int | None = None,
    unresolved_count: int | None = None,
    error_type: ETLErrorType | None = None,
    processing_time_ms: float | None = None,
) -> dict[str, str | int | float]:
    """Build a structured, non-sensitive ETL log event.

    Counts and timings are technical metadata. Payload values, Kafka keys,
    identifiers, addresses, emails, IBANs and other PII are deliberately outside this
    interface.
    """

    _require_allowed("stage", stage, _ALLOWED_STAGES)
    _require_allowed("status", status, _ALLOWED_STATUSES)
    _require_optional_allowed("domain", domain, _ALLOWED_DOMAINS)
    _require_optional_allowed("error_type", error_type, _ALLOWED_ERROR_TYPES)

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
    stage: ETLStage,
    status: ETLStatus,
    domain: ETLDomain | None = None,
    input_count: int | None = None,
    output_count: int | None = None,
    unresolved_count: int | None = None,
    error_type: ETLErrorType | None = None,
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
    logger.info(
        json.dumps(
            event,
            allow_nan=False,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def _require_allowed(field: str, value: str, allowed_values: frozenset[str]) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field} must be one of the allowed technical values")


def _require_optional_allowed(
    field: str,
    value: str | None,
    allowed_values: frozenset[str],
) -> None:
    if value is not None:
        _require_allowed(field, value, allowed_values)


def _add_optional_text(
    event: dict[str, str | int | float],
    field: str,
    value: str | None,
) -> None:
    if value is not None:
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
        if value < 0 or not math.isfinite(value):
            raise ValueError("processing_time_ms must be finite and greater than or equal to 0")
        event["processing_time_ms"] = round(value, 3)


__all__: list[str] = [
    "ETLDomain",
    "ETLErrorType",
    "ETLStage",
    "ETLStatus",
    "build_etl_log_event",
    "log_etl_event",
]
