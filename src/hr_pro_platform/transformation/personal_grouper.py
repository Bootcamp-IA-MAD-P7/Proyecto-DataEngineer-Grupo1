"""Domain-local operational grouping for Personal fragments."""

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Final, Literal, TypeAlias, cast

from .validator import validate_fragment

PERSONAL: Final = "Personal"
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
class PersonalGroup:
    """One deterministic operational bucket keyed by exact ``passport``."""

    key: str
    status: GroupingStatus
    fragments: tuple[JSONPayload, ...]


@dataclass(frozen=True)
class UnresolvedFragment:
    """A fragment that cannot be grouped under the HRP-61 contract."""

    status: UnresolvedStatus
    payload: JSONValue
    classification: str
    reason: str


@dataclass(frozen=True)
class PersonalGroupingResult:
    """Pure grouping output with explicit unresolved outcomes."""

    groups: tuple[PersonalGroup, ...]
    unresolved: tuple[UnresolvedFragment, ...]


def group_personal_fragments(
    fragments: Iterable[ClassifiedFragment],
) -> PersonalGroupingResult:
    """Group validated Personal fragments by exact ``passport``."""

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

        if fragment.classification != PERSONAL:
            unresolved.append(
                UnresolvedFragment(
                    status="unsupported",
                    payload=fragment.payload,
                    classification=fragment.classification,
                    reason="not_personal_fragment",
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
        PersonalGroup(
            key=key,
            status="grouped" if len(payloads) == 1 else "ambiguous",
            fragments=tuple(sorted(payloads, key=_canonical_value)),
        )
        for key, payloads in sorted(buckets.items())
    )
    return PersonalGroupingResult(
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
