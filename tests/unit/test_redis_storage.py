from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from hr_pro_platform.storage.redis import (
    RedisPartialStateStore,
    build_partial_state_key,
    serialize_fragment,
)
from hr_pro_platform.transformation.fragment_contract import ClassifiedFragment


@dataclass
class FakeRedis:
    values: dict[str, set[str]] = field(default_factory=dict)
    fail: Exception | None = None
    closed: bool = False
    expiration_calls: list[tuple[str, ...]] = field(default_factory=list)

    def sadd(self, name: str, value: str) -> int:
        if self.fail is not None:
            raise self.fail
        members = self.values.setdefault(name, set())
        before = len(members)
        members.add(value)
        return int(len(members) > before)

    def close(self) -> None:
        self.closed = True

    def expire(self, *args: Any) -> None:
        self.expiration_calls.append(("expire", *(str(arg) for arg in args)))

    def pexpire(self, *args: Any) -> None:
        self.expiration_calls.append(("pexpire", *(str(arg) for arg in args)))

    def setex(self, *args: Any) -> None:
        self.expiration_calls.append(("setex", *(str(arg) for arg in args)))


def fragment(payload: dict[str, Any], source_reference: str = "source-1") -> ClassifiedFragment:
    return ClassifiedFragment(
        payload=payload,
        classification="Personal",
        source_reference=source_reference,
    )


def test_builds_opaque_provisional_component_key() -> None:
    assert build_partial_state_key("component-a") == "hrp:partial:component-a"
    with pytest.raises(ValueError):
        build_partial_state_key("")


def test_serialization_is_deterministic_and_preserves_provenance() -> None:
    left = fragment({"passport": "P-1", "name": "Ada"})
    right = fragment({"name": "Ada", "passport": "P-1"})

    assert serialize_fragment(left) == serialize_fragment(right)
    assert '"classification":"Personal"' in serialize_fragment(left)
    assert '"source_reference":"source-1"' in serialize_fragment(left)


def test_first_and_second_fragments_accumulate_without_replacement() -> None:
    client = FakeRedis()
    store = RedisPartialStateStore(client=client)
    store.connect()

    assert store.store_fragment("component-a", fragment({"name": "Ada"})) is True
    assert store.store_fragment("component-a", fragment({"passport": "P-1"}, "source-2")) is True

    assert len(client.values["hrp:partial:component-a"]) == 2


def test_exact_duplicate_is_idempotent() -> None:
    client = FakeRedis()
    store = RedisPartialStateStore(client=client)
    store.connect()
    item = fragment({"name": "Ada", "passport": "P-1"})

    assert store.store_fragment("component-a", item) is True
    assert store.store_fragment("component-a", item) is False
    assert len(client.values["hrp:partial:component-a"]) == 1


def test_conflicting_evidence_and_incomplete_fragment_are_preserved() -> None:
    client = FakeRedis()
    store = RedisPartialStateStore(client=client)
    store.connect()

    assert store.store_fragment("component-a", fragment({"name": "Ada"})) is True
    assert store.store_fragment("component-a", fragment({"name": "Different"}, "source-2")) is True

    assert len(client.values["hrp:partial:component-a"]) == 2


def test_redis_failure_is_propagated_without_adapter_retry() -> None:
    client = FakeRedis(fail=ConnectionError("synthetic failure"))
    store = RedisPartialStateStore(client=client)
    store.connect()

    with pytest.raises(ConnectionError, match="synthetic failure"):
        store.store_fragment("component-a", fragment({"name": "Ada"}))


def test_store_does_not_assign_ttl_or_expose_retrieval_api() -> None:
    client = FakeRedis()
    store = RedisPartialStateStore(client=client)
    store.connect()

    store.store_fragment("component-a", fragment({"name": "Ada"}))

    assert client.expiration_calls == []
    assert not hasattr(store, "retrieve_fragments")
