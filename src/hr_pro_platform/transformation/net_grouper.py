"""Domain-local operational grouping for Net fragments."""

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Final, Literal, cast

from .fragment_contract import (
    ClassifiedFragment,
    GroupedFragment,
    JSONPayload,
    UnresolvedFragment,
)
from .fragment_contract import (
    JSONValue as JSONValue,
)
from .validator import validate_fragment

NET: Final = "Net"
GroupingStatus = Literal["grouped", "ambiguous"]


@dataclass(frozen=True)
class NetGroup:
    """One deterministic bucket keyed by exact ``address``."""

    key: str
    status: GroupingStatus
    fragments: tuple[GroupedFragment, ...]


@dataclass(frozen=True)
class NetGroupingResult:
    """Pure grouping output with explicit unresolved outcomes."""

    groups: tuple[NetGroup, ...]
    unresolved: tuple[UnresolvedFragment, ...]


def group_net_fragments(
    fragments: Iterable[ClassifiedFragment],
) -> NetGroupingResult:
    """Group validated Net fragments by exact ``address``."""

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

        if fragment.classification != NET:
            unresolved.append(
                UnresolvedFragment(
                    status="unsupported",
                    payload=fragment.payload,
                    classification=fragment.classification,
                    source_reference=fragment.source_reference,
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
                    source_reference=fragment.source_reference,
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
                    source_reference=fragment.source_reference,
                    reason="address_unusable",
                )
            )
            continue

        grouped_fragment = GroupedFragment(
            payload=json_payload,
            source_reference=fragment.source_reference,
        )
        bucket = buckets.setdefault(address, [])
        if grouped_fragment not in bucket:
            bucket.append(grouped_fragment)

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
