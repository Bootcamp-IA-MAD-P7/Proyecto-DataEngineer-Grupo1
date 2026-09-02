"""Shared typed fragment contracts for transformation stages."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, TypeAlias

JSONValue: TypeAlias = None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]
JSONPayload: TypeAlias = Mapping[str, JSONValue]

# Opaque, upstream-supplied and non-sensitive. HRP-50 deliberately does not
# assign this value database, Kafka, UUID or business-identity semantics.
SourceReference: TypeAlias = str
UnresolvedStatus: TypeAlias = Literal["uncorrelated", "unsupported"]


@dataclass(frozen=True)
class ClassifiedFragment:
    """A source fragment with upstream classification and provenance."""

    payload: JSONValue
    classification: str
    source_reference: SourceReference


@dataclass(frozen=True)
class GroupedFragment:
    """Payload evidence plus its opaque upstream source reference."""

    payload: JSONPayload
    source_reference: SourceReference


@dataclass(frozen=True)
class UnresolvedFragment:
    """A classified fragment that a domain grouper could not group."""

    status: UnresolvedStatus
    payload: JSONValue
    classification: str
    source_reference: SourceReference
    reason: str
