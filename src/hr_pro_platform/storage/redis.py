"""Temporary Redis storage for classified partial person fragments."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Protocol, cast

from redis import Redis

from ..transformation.fragment_contract import ClassifiedFragment, JSONValue

REDIS_URL = "REDIS_URL"
PARTIAL_STATE_TTL_SECONDS = "HRP_REDIS_PARTIAL_STATE_TTL_SECONDS"
DEFAULT_PARTIAL_STATE_TTL_SECONDS = 3600
KEY_PREFIX = "hrp:partial:"


class RedisSetClient(Protocol):
    def sadd(self, name: str, value: str) -> int: ...

    def expire(self, name: str, time: int) -> bool: ...

    def close(self) -> None: ...


def build_partial_state_key(component_identifier: str) -> str:
    """Build a key for an opaque provisional correlation component."""

    if not component_identifier:
        raise ValueError("component_identifier must not be empty")
    return f"{KEY_PREFIX}{component_identifier}"


def parse_partial_state_ttl(raw_value: str) -> int:
    """Validate a configured Redis partial-state TTL expressed in seconds."""

    if not raw_value or not raw_value.isdecimal():
        raise ValueError(f"{PARTIAL_STATE_TTL_SECONDS} must be a positive integer")
    ttl_seconds = int(raw_value)
    if ttl_seconds <= 0:
        raise ValueError(f"{PARTIAL_STATE_TTL_SECONDS} must be a positive integer")
    return ttl_seconds


def resolve_partial_state_ttl(raw_value: str | None = None) -> int:
    """Resolve the partial-state TTL from an explicit value or the environment."""

    configured_value = os.environ.get(PARTIAL_STATE_TTL_SECONDS) if raw_value is None else raw_value
    if configured_value is None:
        return DEFAULT_PARTIAL_STATE_TTL_SECONDS
    return parse_partial_state_ttl(configured_value)


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


class RedisPartialStateStore:
    """Write-only HRP-74 boundary for temporary classified fragment state."""

    def __init__(
        self,
        redis_url: str | None = None,
        client: RedisSetClient | None = None,
        ttl_seconds: int | None = None,
    ) -> None:
        self._redis_url = redis_url or os.environ.get(REDIS_URL)
        self._client = client
        if ttl_seconds is None:
            self._ttl_seconds = resolve_partial_state_ttl()
        elif isinstance(ttl_seconds, bool) or ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be a positive integer")
        else:
            self._ttl_seconds = ttl_seconds

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
        key = build_partial_state_key(component_identifier)
        added = self._client.sadd(key, serialize_fragment(fragment))
        self._client.expire(key, self._ttl_seconds)
        return added == 1


__all__ = [
    "DEFAULT_PARTIAL_STATE_TTL_SECONDS",
    "KEY_PREFIX",
    "PARTIAL_STATE_TTL_SECONDS",
    "RedisPartialStateStore",
    "build_partial_state_key",
    "parse_partial_state_ttl",
    "resolve_partial_state_ttl",
    "serialize_fragment",
]
