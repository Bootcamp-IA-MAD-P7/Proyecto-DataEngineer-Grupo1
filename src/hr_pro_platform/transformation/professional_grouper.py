"""Domain-local operational grouping for Professional fragments."""

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Final, Literal, TypeAlias, cast

from .validator import validate_fragment

PROFESSIONAL: Final = "Professional"
GroupingStatus = Literal["grouped", "ambiguous"]
UnresolvedStatus = Literal["uncorrelated", "unsupported"]
JSONValue: TypeAlias = None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]
JSONPayload: TypeAlias = Mapping[str, JSONValue]


@dataclass(frozen=True)
class ClassifiedFragment:
    """A fragment together with its upstream classification context."""

    payload: JSONValue
    classification: str


@dataclass(frozen=True)
class ProfessionalGroup:
    """One deterministic bucket keyed by exact ``fullname``."""

    key: str
    status: GroupingStatus
    fragments: tuple[JSONPayload, ...]


@dataclass(frozen=True)
class UnresolvedFragment:
    """A fragment that cannot be grouped under the HRP-47 contract."""

    status: UnresolvedStatus
    payload: JSONValue
    classification: str
    reason: str


@dataclass(frozen=True)
class ProfessionalGroupingResult:
    """Pure grouping output with explicit unresolved outcomes."""

    groups: tuple[ProfessionalGroup, ...]
    unresolved: tuple[UnresolvedFragment, ...]


def group_professional_fragments(
    fragments: Iterable[ClassifiedFragment],
) -> ProfessionalGroupingResult:
    """Group validated Professional fragments by exact ``fullname``."""

    buckets: dict[str, list[JSONPayload]] = {}
    unresolved: list[UnresolvedFragment] = []

    for fragment in fragments:
        validation = validate_fragment(fragment.payload, fragment.classification)
        if not validation.is_valid:
            unresolved.append(
                UnresolvedFragment(
                    status="unsupported",
                    payload=fragment.payload,
                    classification=fragment.classification,
                    reason=validation.errors[0],
                )
            )
            continue

        if fragment.classification != PROFESSIONAL:
            unresolved.append(
                UnresolvedFragment(
                    status="unsupported",
                    payload=fragment.payload,
                    classification=fragment.classification,
                    reason="not_professional_fragment",
                )
            )
            continue

        payload = validation.payload
        if not isinstance(payload, Mapping):
            unresolved.append(
                UnresolvedFragment(
                    status="unsupported",
                    payload=fragment.payload,
                    classification=fragment.classification,
                    reason="payload_not_mapping",
                )
            )
            continue
        json_payload = cast(JSONPayload, payload)
        fullname = json_payload.get("fullname")
        if not isinstance(fullname, str) or fullname == "":
            unresolved.append(
                UnresolvedFragment(
                    status="uncorrelated",
                    payload=fragment.payload,
                    classification=fragment.classification,
                    reason="fullname_unusable",
                )
            )
            continue

        bucket = buckets.setdefault(fullname, [])
        if not any(existing == json_payload for existing in bucket):
            bucket.append(json_payload)

    groups = tuple(
        ProfessionalGroup(
            key=key,
            status="grouped" if len(payloads) == 1 else "ambiguous",
            fragments=tuple(sorted(payloads, key=_canonical_value)),
        )
        for key, payloads in sorted(buckets.items())
    )
    return ProfessionalGroupingResult(
        groups=groups,
        unresolved=tuple(
            sorted(
                unresolved,
                key=lambda item: (
                    item.status,
                    item.reason,
                    item.classification,
                    _canonical_value(item.payload),
                ),
            )
        ),
    )


def _canonical_value(value: object) -> str:
    """Return a stable ordering representation for JSON-compatible values."""

    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
