"""Pure validation boundary for classified event fragments."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from .classifier import DOMAIN_FIELDS, UNKNOWN

SUPPORTED_CLASSIFICATIONS: Final[frozenset[str]] = frozenset(DOMAIN_FIELDS)


@dataclass(frozen=True)
class ValidationResult:
    """Explicit outcome of validating one transformation-stage fragment."""

    is_valid: bool
    classification: str
    errors: tuple[str, ...]
    payload: Mapping[str, object] | None


def validate_fragment(payload: object, classification: str) -> ValidationResult:
    """Validate only the approved technical transformation boundary.

    This function deliberately performs no semantic value validation or cleaning.
    """

    if not isinstance(payload, Mapping):
        return ValidationResult(
            is_valid=False,
            classification=classification,
            errors=("payload_not_mapping",),
            payload=None,
        )

    if classification == UNKNOWN or classification not in SUPPORTED_CLASSIFICATIONS:
        return ValidationResult(
            is_valid=False,
            classification=classification,
            errors=("unsupported_classification",),
            payload=payload,
        )

    return ValidationResult(
        is_valid=True,
        classification=classification,
        errors=(),
        payload=payload,
    )
