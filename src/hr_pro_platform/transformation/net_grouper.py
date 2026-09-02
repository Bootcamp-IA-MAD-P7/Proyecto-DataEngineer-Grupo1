"""Domain-local operational grouping for Net fragments."""

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Final, Literal, TypeAlias, cast

from .validator import validate_fragment

NET: Final = "Net"
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
class NetGroup:
    """One deterministic bucket keyed by exact ``address``."""

    key: str
    status: GroupingStatus
    fragments: tuple[JSONPayload, ...]


@dataclass(frozen=True)
class UnresolvedFragment:
    """A fragment that cannot be grouped under the HRP-49 contract."""

    status: UnresolvedStatus
    payload: JSONValue
    classification: str
    reason: str


@dataclass(frozen=True)
class NetGroupingResult:
    """Pure grouping output with explicit unresolved outcomes."""

    groups: tuple[NetGroup, ...]
    unresolved: tuple[UnresolvedFragment, ...]


def group_net_fragments(
    fragments: Iterable[ClassifiedFragment],
) -> NetGroupingResult:
    """Group validated Net fragments by exact ``address``."""

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

        if fragment.classification != NET:
            unresolved.append(
                UnresolvedFragment(
                    status="unsupported",
                    payload=fragment.payload,
                    classification=fragment.classification,
                    reason="not_net_fragment",
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
        address = json_payload.get("address")
        if not isinstance(address, str) or address == "":
            unresolved.append(
                UnresolvedFragment(
                    status="uncorrelated",
                    payload=fragment.payload,
                    classification=fragment.classification,
                    reason="address_unusable",
                )
            )
            continue

        bucket = buckets.setdefault(address, [])
        if not any(existing == json_payload for existing in bucket):
            bucket.append(json_payload)

    groups = tuple(
        NetGroup(
            key=key,
            status="grouped" if len(payloads) == 1 else "ambiguous",
            fragments=tuple(sorted(payloads, key=_canonical_value)),
        )
        for key, payloads in sorted(buckets.items())
    )
    return NetGroupingResult(
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
