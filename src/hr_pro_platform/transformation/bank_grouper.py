"""Domain-local operational grouping for Bank fragments."""

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Final, Literal, TypeAlias, cast

from .validator import validate_fragment

BANK: Final = "Bank"
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
class BankGroup:
    """One deterministic bucket keyed by exact ``passport``."""

    key: str
    status: GroupingStatus
    fragments: tuple[JSONPayload, ...]


@dataclass(frozen=True)
class UnresolvedFragment:
    """A fragment that cannot be grouped under the HRP-48 contract."""

    status: UnresolvedStatus
    payload: JSONValue
    classification: str
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

        if fragment.classification != BANK:
            unresolved.append(
                UnresolvedFragment(
                    status="unsupported",
                    payload=fragment.payload,
                    classification=fragment.classification,
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
                    reason="passport_unusable",
                )
            )
            continue

        bucket = buckets.setdefault(passport, [])
        if not any(existing == json_payload for existing in bucket):
            bucket.append(json_payload)

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
                    _canonical_value(item.payload),
                ),
            )
        ),
    )


def _canonical_value(value: object) -> str:
    """Return a stable ordering representation for JSON-compatible values."""

    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
