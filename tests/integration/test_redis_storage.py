from __future__ import annotations

import os
import uuid

import pytest
from redis import Redis

from hr_pro_platform.storage.redis import (
    MalformedFragmentError,
    RedisPartialStateStore,
    serialize_fragment,
)
from hr_pro_platform.transformation.fragment_contract import ClassifiedFragment


@pytest.fixture
def live_redis() -> Redis:
    url = os.environ.get("HRP74_REDIS_URL")
    if not url:
        pytest.skip("HRP74_REDIS_URL is not configured for Redis integration")
    client = Redis.from_url(url, decode_responses=True)
    try:
        client.ping()
    except Exception as exc:
        pytest.skip(f"Redis is not available: {type(exc).__name__}")
    return client


def test_real_redis_accumulates_idempotent_and_conflicting_fragments(
    live_redis: Redis,
) -> None:
    component = f"integration-{uuid.uuid4()}"
    key = f"hrp:partial:{component}"
    store = RedisPartialStateStore(client=live_redis)
    first = ClassifiedFragment({"name": "Ada"}, "Personal", "source-1")
    second = ClassifiedFragment({"passport": "P-1"}, "Bank", "source-2")
    conflict = ClassifiedFragment({"name": "Different"}, "Personal", "source-3")

    try:
        assert store.store_fragment(component, first) is True
        assert store.store_fragment(component, second) is True
        assert store.store_fragment(component, first) is False
        assert store.store_fragment(component, conflict) is True

        members = live_redis.smembers(key)
        assert len(members) == 3
        assert any('"source_reference":"source-1"' in member for member in members)
        assert any('"source_reference":"source-2"' in member for member in members)
        assert any('"source_reference":"source-3"' in member for member in members)
        assert live_redis.ttl(key) == -1
    finally:
        live_redis.delete(key)


def test_real_redis_stores_and_retrieves_one_fragment(live_redis: Redis) -> None:
    component = f"integration-{uuid.uuid4()}"
    key = f"hrp:partial:{component}"
    store = RedisPartialStateStore(client=live_redis)
    expected = ClassifiedFragment({"name": "Ada"}, "Personal", "source-1")

    try:
        store.store_fragment(component, expected)
        assert store.retrieve_fragments(component) == (expected,)
    finally:
        live_redis.delete(key)


def test_real_redis_retrieval_preserves_multiple_conflicting_fragments(
    live_redis: Redis,
) -> None:
    component = f"integration-{uuid.uuid4()}"
    key = f"hrp:partial:{component}"
    store = RedisPartialStateStore(client=live_redis)
    fragments = {
        ClassifiedFragment({"name": "Ada"}, "Personal", "source-1"),
        ClassifiedFragment({"name": "Different"}, "Personal", "source-2"),
    }

    try:
        for item in fragments:
            store.store_fragment(component, item)
        retrieved = store.retrieve_fragments(component)
        assert {serialize_fragment(item) for item in retrieved} == {
            serialize_fragment(item) for item in fragments
        }
    finally:
        live_redis.delete(key)


def test_real_redis_missing_component_returns_empty_tuple(live_redis: Redis) -> None:
    store = RedisPartialStateStore(client=live_redis)

    assert store.retrieve_fragments(f"missing-{uuid.uuid4()}") == ()


def test_real_redis_malformed_member_fails_and_set_remains_unchanged(
    live_redis: Redis,
) -> None:
    component = f"integration-{uuid.uuid4()}"
    key = f"hrp:partial:{component}"

    try:
        live_redis.sadd(key, "not-json")
        before = live_redis.smembers(key)
        store = RedisPartialStateStore(client=live_redis)

        with pytest.raises(MalformedFragmentError):
            store.retrieve_fragments(component)

        assert live_redis.smembers(key) == before
    finally:
        live_redis.delete(key)
