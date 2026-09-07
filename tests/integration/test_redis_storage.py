from __future__ import annotations

import os
import time
import uuid

import pytest
from redis import Redis

from hr_pro_platform.storage.redis import RedisPartialStateStore, serialize_fragment
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
    store = RedisPartialStateStore(client=live_redis, ttl_seconds=60)
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
        assert 0 < live_redis.ttl(key) <= 60
    finally:
        live_redis.delete(key)


def test_real_redis_refreshes_ttl_for_new_duplicate_and_conflicting_fragments(
    live_redis: Redis,
) -> None:
    component = f"integration-{uuid.uuid4()}"
    key = f"hrp:partial:{component}"
    store = RedisPartialStateStore(client=live_redis, ttl_seconds=2)
    first = ClassifiedFragment({"name": "Ada"}, "Personal", "source-1")
    conflict = ClassifiedFragment({"name": "Different"}, "Personal", "source-2")

    try:
        assert store.store_fragment(component, first) is True
        first_ttl = live_redis.ttl(key)
        assert 0 < first_ttl <= 2
        time.sleep(1.1)

        assert store.store_fragment(component, first) is False
        refreshed_ttl = live_redis.ttl(key)
        assert refreshed_ttl > 0
        assert refreshed_ttl > first_ttl - 1

        assert store.store_fragment(component, conflict) is True
        assert live_redis.smembers(key) == {
            serialize_fragment(first),
            serialize_fragment(conflict),
        }
    finally:
        live_redis.delete(key)


def test_real_redis_expiration_removes_idle_partial_state(live_redis: Redis) -> None:
    component = f"integration-{uuid.uuid4()}"
    key = f"hrp:partial:{component}"
    store = RedisPartialStateStore(client=live_redis, ttl_seconds=1)

    try:
        store.store_fragment(component, ClassifiedFragment({"name": "Ada"}, "Personal", "source-1"))
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline and live_redis.exists(key):
            time.sleep(0.1)
        assert live_redis.exists(key) == 0
    finally:
        live_redis.delete(key)
