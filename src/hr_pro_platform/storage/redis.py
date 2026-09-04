"""Temporary Redis storage for classified partial person fragments."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Protocol, cast

from redis import Redis

from ..transformation.fragment_contract import ClassifiedFragment, JSONValue

REDIS_URL = "REDIS_URL"
KEY_PREFIX = "hrp:partial:"


class RedisSetClient(Protocol):
    def sadd(self, name: str, value: str) -> int: ...

    def smembers(self, name: str) -> set[str]: ...

    def close(self) -> None: ...


class MalformedFragmentError(ValueError):
    """Raised when a Redis Set member is not a valid stored fragment."""


def build_partial_state_key(component_identifier: str) -> str:
    """Build a key for an opaque provisional correlation component."""

    if not component_identifier:
        raise ValueError("component_identifier must not be empty")
    return f"{KEY_PREFIX}{component_identifier}"


def serialize_fragment(fragment: ClassifiedFragment) -> str:
    """Serialize one classified fragment deterministically for Set membership."""

    if not isinstance(fragment.payload, Mapping):
        raise ValueError("classified fragment payload must be a JSON object")
    if not fragment.classification:
        raise ValueError("classified fragment classification must not be empty")
    if not fragment.source_reference:
        raise ValueError("classified fragment source_reference must not be empty")

    value: dict[str, JSONValue] = {
        "classification": fragment.classification,
        "payload": dict(fragment.payload),
        "source_reference": fragment.source_reference,
    }
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _deserialize_fragment(member: str) -> ClassifiedFragment:
    """Deserialize one HRP-74 Set member without discarding invalid data."""

    try:
        value = json.loads(member)
    except (json.JSONDecodeError, TypeError) as exc:
        raise MalformedFragmentError("stored Redis fragment is not valid JSON") from exc

    if not isinstance(value, dict) or set(value) != {
        "classification",
        "payload",
        "source_reference",
    }:
        raise MalformedFragmentError("stored Redis fragment has an invalid structure")

    classification = value["classification"]
    payload = value["payload"]
    source_reference = value["source_reference"]
    if not isinstance(classification, str) or not classification:
        raise MalformedFragmentError("stored Redis fragment has an invalid classification")
    if not isinstance(payload, Mapping):
        raise MalformedFragmentError("stored Redis fragment has an invalid payload")
    if not isinstance(source_reference, str) or not source_reference:
        raise MalformedFragmentError("stored Redis fragment has an invalid source reference")

    return ClassifiedFragment(
        payload=cast(JSONValue, payload),
        classification=classification,
        source_reference=source_reference,
    )


class RedisPartialStateStore:
    """Redis boundary for temporary classified fragment state."""

    def __init__(self, redis_url: str | None = None, client: RedisSetClient | None = None) -> None:
        self._redis_url = redis_url or os.environ.get(REDIS_URL)
        self._client = client

    def connect(self) -> None:
        if self._client is None:
            if not self._redis_url:
                raise OSError("Missing required environment variable: REDIS_URL")
            self._client = cast(
                RedisSetClient, Redis.from_url(self._redis_url, decode_responses=True)
            )

    def close(self) -> None:
        if self._client is not None:
            self._client.close()

    def store_fragment(self, component_identifier: str, fragment: ClassifiedFragment) -> bool:
        """Accumulate a fragment and return whether it was newly added."""

        if self._client is None:
            raise RuntimeError("Redis client is not connected")
        added = self._client.sadd(
            build_partial_state_key(component_identifier), serialize_fragment(fragment)
        )
        return added == 1

    def retrieve_fragments(self, component_identifier: str) -> tuple[ClassifiedFragment, ...]:
        """Retrieve every stored fragment for an opaque provisional component."""

        if self._client is None:
            raise RuntimeError("Redis client is not connected")
        key = build_partial_state_key(component_identifier)
        return tuple(_deserialize_fragment(member) for member in self._client.smembers(key))


__all__ = [
    "KEY_PREFIX",
    "MalformedFragmentError",
    "RedisPartialStateStore",
    "build_partial_state_key",
    "serialize_fragment",
]
