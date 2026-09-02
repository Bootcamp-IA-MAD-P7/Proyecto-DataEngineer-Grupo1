"""Domain-local operational grouping for Professional fragments."""

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Final, Literal, cast

from .fragment_contract import (
    ClassifiedFragment,
    GroupedFragment,
    JSONPayload,
    JSONValue,
    SourceReference,
)
from .validator import validate_fragment

PROFESSIONAL: Final = "Professional"
GroupingStatus = Literal["grouped", "ambiguous"]
UnresolvedStatus = Literal["uncorrelated", "unsupported"]


@dataclass(frozen=True)
class ProfessionalGroup:
    """One deterministic bucket keyed by exact ``fullname``."""

    key: str
    status: GroupingStatus
    fragments: tuple[GroupedFragment, ...]


@dataclass(frozen=True)
class UnresolvedFragment:
    """A fragment that cannot be grouped under the HRP-47 contract."""

    status: UnresolvedStatus
    payload: JSONValue
    classification: str
    source_reference: SourceReference
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

    buckets: dict[str, list[GroupedFragment]] = {}
    unresolved: list[UnresolvedFragment] = []

    for fragment in fragments:
        validation = validate_fragment(fragment.payload, fragment.classification)
        if not validation.is_valid:
            unresolved.append(
                UnresolvedFragment(
                    status="unsupported",
                    payload=fragment.payload,
                    classification=fragment.classification,
                    source_reference=fragment.source_reference,
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
                    source_reference=fragment.source_reference,
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
                    source_reference=fragment.source_reference,
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
                    source_reference=fragment.source_reference,
                    reason="fullname_unusable",
                )
            )
            continue

        grouped_fragment = GroupedFragment(
            payload=json_payload,
            source_reference=fragment.source_reference,
        )
        bucket = buckets.setdefault(fullname, [])
        if grouped_fragment not in bucket:
            bucket.append(grouped_fragment)

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
                    item.source_reference,
                    _canonical_value(item.payload),
                ),
            )
        ),
    )


def _canonical_value(value: object) -> str:
    """Return a stable ordering representation for JSON-compatible values."""

    if isinstance(value, GroupedFragment):
        value = (value.payload, value.source_reference)
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
