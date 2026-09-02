"""Domain-local operational grouping for Location fragments."""

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Final, Literal, TypeAlias, cast

from .validator import validate_fragment

LOCATION: Final = "Location"
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
class LocationGroup:
    """One deterministic operational bucket keyed by exact ``fullname``."""

    key: str
    status: GroupingStatus
    fragments: tuple[JSONPayload, ...]


@dataclass(frozen=True)
class UnresolvedFragment:
    """A fragment that cannot be grouped under the HRP-46 contract."""

    status: UnresolvedStatus
    payload: JSONValue
    reason: str


@dataclass(frozen=True)
class LocationGroupingResult:
    """Pure grouping output with explicit unresolved outcomes."""

    groups: tuple[LocationGroup, ...]
    unresolved: tuple[UnresolvedFragment, ...]


def group_location_fragments(
    fragments: Iterable[ClassifiedFragment],
) -> LocationGroupingResult:
    """Group validated Location fragments by exact ``fullname``.

    The function does not normalize values, create identity keys, or mutate any
    input. Invalid or non-Location fragments are retained as unresolved output.
    """

    buckets: dict[str, list[JSONPayload]] = {}
    unresolved: list[UnresolvedFragment] = []

    for fragment in fragments:
        validation = validate_fragment(fragment.payload, fragment.classification)
        if not validation.is_valid:
            unresolved.append(
                UnresolvedFragment(
                    status="unsupported",
                    payload=fragment.payload,
                    reason=validation.errors[0],
                )
            )
            continue

        if fragment.classification != LOCATION:
            unresolved.append(
                UnresolvedFragment(
                    status="unsupported",
                    payload=fragment.payload,
                    reason="not_location_fragment",
                )
            )
            continue

        payload = validation.payload
        if not isinstance(payload, Mapping):
            unresolved.append(
                UnresolvedFragment(
                    status="unsupported",
                    payload=fragment.payload,
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
                    reason="fullname_unusable",
                )
            )
            continue

        bucket = buckets.setdefault(fullname, [])
        if not any(existing == json_payload for existing in bucket):
            bucket.append(json_payload)

    groups = tuple(
        LocationGroup(
            key=key,
            status="grouped" if len(payloads) == 1 else "ambiguous",
            fragments=tuple(sorted(payloads, key=_canonical_value)),
        )
        for key, payloads in sorted(buckets.items())
    )
    ordered_unresolved = tuple(
        sorted(
            unresolved, key=lambda item: (item.status, item.reason, _canonical_value(item.payload))
        )
    )
    return LocationGroupingResult(groups=groups, unresolved=ordered_unresolved)


def _canonical_value(value: object) -> str:
    """Return a stable ordering representation for JSON-compatible values."""

    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
