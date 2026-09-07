# HRP-76 — Configure expiration of temporary Redis data

**Status:** Implementation validated — PR #70 pending human approval and merge
**Owner:** Gabriela Granja
**Jira:** HRP-76
**Dependencies:** HRP-73, HRP-74
**Related spec:** [HRP-74](HRP-74-store-partial-person-data-redis.md)

## Objective

Ensure that temporary partial person state stored in Redis is bounded by a
configurable time-to-live (TTL), while preserving the existing HRP-74 storage
contract and Redis Set semantics.

## Context and scope

- Includes: TTL configuration, positive-integer validation, applying expiration to
  each partial-state Redis key, refreshing expiration when storage is attempted.
- Excludes: Redis retrieval, ETL integration, final person records, monitoring,
  Prometheus and changes to correlation rules.
- Assumption: Redis partial state is temporary and MongoDB remains the recoverable
  raw source.
- Risk: an invalid TTL configuration must fail clearly rather than create
  unbounded temporary state.

## Design

The existing `RedisPartialStateStore` resolves
`HRP_REDIS_PARTIAL_STATE_TTL_SECONDS` from the environment, defaulting to `3600`
seconds when it is absent. The value must be a positive decimal integer; zero,
negative and non-numeric values are rejected with `ValueError`.

After `SADD` stores a fragment under
`hrp:partial:{provisional_component_identifier}`, the same key receives Redis
`EXPIRE` with the configured number of seconds. This is also executed for an
exact duplicate, so a newly received fragment attempt refreshes the temporary
state window. Redis errors from `SADD` or `EXPIRE` are surfaced to the caller;
the adapter does not silently report success or add retry policy.

The change does not alter deterministic serialization, Set accumulation,
idempotency, conflict preservation or the approved opaque correlation boundary
from HRP-74.

## Acceptance criteria

- [x] The partial-state TTL is configurable through
  `HRP_REDIS_PARTIAL_STATE_TTL_SECONDS`.
- [x] The default TTL is 3600 seconds when the variable is absent.
- [x] Zero, negative and non-numeric TTL values are rejected.
- [x] `EXPIRE` is applied to the Redis key after a fragment storage operation.
- [x] A subsequent duplicate or distinct fragment refreshes the key TTL.
- [x] Redis `SADD` and `EXPIRE` failures are propagated without silent success.
- [x] Existing HRP-74 Set serialization, accumulation and idempotency behavior is
  preserved.
- [x] Unit tests cover configuration and failure behavior, and Redis integration
  tests demonstrate TTL refresh and expiration.
- [x] The spec passes the repository specification validator.

## Accessibility and sustainability applicability

- Accessibility: not applicable — this is an internal backend storage capability
  with no user-facing flow.
- Sustainability: applicable — TTL bounds temporary retained state and avoids
  indefinite Redis resource use. Evidence is the configured expiration and runtime
  expiration integration test.
- Deferred claims: no carbon, energy or deployment-efficiency claim is made.

## Testing

| Level | Case | Evidence |
|---|---|---|
| Unitario | Default/configured TTL, invalid values, refresh call and failures | `tests/unit/test_redis_storage.py` — 27 passed |
| Integración local/manual | Real Redis TTL assignment, refresh and idle expiration; Redis runtime `PONG` | `tests/integration/test_redis_storage.py` — 7 passed, 0 skipped |
| Static / CI | Spec structure and checks provided by the existing quality workflow | `scripts/validate_specs.py`, Ruff, mypy; CI does not provision Redis |

## Evidence of closure

- Branch: `feature/HRP-76-configure-redis-temporary-data-expiration`
- PR: #70
- Implementation/merge-resolution head used for final validation: `deee457`
- Unit Redis: 27 passed
- Redis integration: 7 passed, 0 skipped against real Redis
- Redis runtime: `PONG`
- Spec validation: PASS
- Ruff: PASS
- mypy: PASS
- CI qualification: Redis integration tests were executed locally/manually against
  real Redis. The current `quality` GitHub Actions workflow does not provision
  Redis, so its green status is not Redis integration evidence.
- Human approval / merge: pending
