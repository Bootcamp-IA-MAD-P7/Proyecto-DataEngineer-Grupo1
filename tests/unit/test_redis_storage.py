from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from hr_pro_platform.storage.redis import (
    MalformedFragmentError,
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
    smembers_fail: Exception | None = None
    smembers_calls: list[str] = field(default_factory=list)

    def sadd(self, name: str, value: str) -> int:
        if self.fail is not None:
            raise self.fail
        members = self.values.setdefault(name, set())
        before = len(members)
        members.add(value)
        return int(len(members) > before)

    def close(self) -> None:
        self.closed = True

    def smembers(self, name: str) -> set[str]:
        if self.smembers_fail is not None:
            raise self.smembers_fail
        self.smembers_calls.append(name)
        return set(self.values.get(name, set()))

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


def test_retrieves_one_fragment_and_preserves_all_fields() -> None:
    client = FakeRedis()
    store = RedisPartialStateStore(client=client)
    fragment_to_store = fragment({"name": "Ada"})
    store.connect()
    store.store_fragment("component-a", fragment_to_store)

    assert store.retrieve_fragments("component-a") == (fragment_to_store,)


def test_retrieves_multiple_conflicting_fragments_without_resolution() -> None:
    client = FakeRedis()
    store = RedisPartialStateStore(client=client)
    first = fragment({"name": "Ada"})
    second = fragment({"name": "Different"}, "source-2")
    store.connect()
    store.store_fragment("component-a", first)
    store.store_fragment("component-a", second)

    retrieved = store.retrieve_fragments("component-a")
    assert {serialize_fragment(item) for item in retrieved} == {
        serialize_fragment(first),
        serialize_fragment(second),
    }


def test_missing_component_returns_empty_tuple() -> None:
    store = RedisPartialStateStore(client=FakeRedis())
    store.connect()

    assert store.retrieve_fragments("missing") == ()


@pytest.mark.parametrize(
    "member",
    [
        "not-json",
        '{"classification":"Personal","payload":{"name":"Ada"}}',
        '{"classification":"Personal","payload":{"name":"Ada"},'
        '"source_reference":"source-1","extra":true}',
        '{"classification":1,"payload":{"name":"Ada"},"source_reference":"source-1"}',
        '{"classification":"Personal","payload":[],"source_reference":"source-1"}',
        '{"classification":"Personal","payload":{"name":"Ada"},"source_reference":false}',
    ],
)
def test_malformed_or_structurally_invalid_member_fails_explicitly(member: str) -> None:
    client = FakeRedis(values={"hrp:partial:component-a": {member}})
    store = RedisPartialStateStore(client=client)
    store.connect()

    with pytest.raises(MalformedFragmentError):
        store.retrieve_fragments("component-a")


def test_smembers_failure_is_propagated_unchanged() -> None:
    failure = ConnectionError("synthetic failure")
    store = RedisPartialStateStore(client=FakeRedis(smembers_fail=failure))
    store.connect()

    with pytest.raises(ConnectionError) as exc_info:
        store.retrieve_fragments("component-a")

    assert exc_info.value is failure


def test_retrieval_is_read_only() -> None:
    client = FakeRedis()
    store = RedisPartialStateStore(client=client)
    store.connect()
    store.store_fragment("component-a", fragment({"name": "Ada"}))
    before = dict(client.values)

    store.retrieve_fragments("component-a")

    assert client.values == before
    assert client.smembers_calls == ["hrp:partial:component-a"]


def test_retrieval_reuses_component_identifier_validation() -> None:
    store = RedisPartialStateStore(client=FakeRedis())
    store.connect()

    with pytest.raises(ValueError, match="component_identifier"):
        store.retrieve_fragments("")
