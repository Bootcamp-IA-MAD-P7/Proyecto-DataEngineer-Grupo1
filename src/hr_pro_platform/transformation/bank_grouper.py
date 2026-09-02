"""Domain-local operational grouping for Bank fragments."""

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

BANK: Final = "Bank"
GroupingStatus = Literal["grouped", "ambiguous"]
UnresolvedStatus = Literal["uncorrelated", "unsupported"]


@dataclass(frozen=True)
class BankGroup:
    """One deterministic bucket keyed by exact ``passport``."""

    key: str
    status: GroupingStatus
    fragments: tuple[GroupedFragment, ...]


@dataclass(frozen=True)
class UnresolvedFragment:
    """A fragment that cannot be grouped under the HRP-48 contract."""

    status: UnresolvedStatus
    payload: JSONValue
    classification: str
    source_reference: SourceReference
    reason: str


@dataclass(frozen=True)
class BankGroupingResult:
    """Pure grouping output with explicit unresolved outcomes."""

    groups: tuple[BankGroup, ...]
    unresolved: tuple[UnresolvedFragment, ...]


def group_bank_fragments(
    fragments: Iterable[ClassifiedFragment],
) -> BankGroupingResult:
    """Group validated Bank fragments by exact ``passport``."""

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

        if fragment.classification != BANK:
            unresolved.append(
                UnresolvedFragment(
                    status="unsupported",
                    payload=fragment.payload,
                    classification=fragment.classification,
                    source_reference=fragment.source_reference,
                    reason="not_bank_fragment",
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
        passport = json_payload.get("passport")
        if not isinstance(passport, str) or passport == "":
            unresolved.append(
                UnresolvedFragment(
                    status="uncorrelated",
                    payload=fragment.payload,
                    classification=fragment.classification,
                    source_reference=fragment.source_reference,
                    reason="passport_unusable",
                )
            )
            continue

        grouped_fragment = GroupedFragment(
            payload=json_payload,
            source_reference=fragment.source_reference,
        )
        bucket = buckets.setdefault(passport, [])
        if grouped_fragment not in bucket:
            bucket.append(grouped_fragment)

    groups = tuple(
        BankGroup(
            key=key,
            status="grouped" if len(payloads) == 1 else "ambiguous",
            fragments=tuple(sorted(payloads, key=_canonical_value)),
        )
        for key, payloads in sorted(buckets.items())
    )
    return BankGroupingResult(
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
