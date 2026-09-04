# HRP-75 — Retrieve partial person data from Redis for the ETL

**Status:** Implemented — pending merge
**Jira:** HRP-75
**Dependencies:** HRP-74, HRP-73, ADR-0006

## Objective

Provide a read-only retrieval operation so ETL stages can consume all classified
fragments stored for an opaque provisional component identifier.

## Dependencies and approved HRP-74 contract

HRP-74 stores temporary correlation state in Redis using:

- key pattern: `hrp:partial:{provisional_component_identifier}`;
- Redis structure: Set;
- member format: canonical JSON containing exactly `classification`, `payload`, and
  `source_reference`.

The identifier remains operational and opaque. It is not a universal or final
`person_id`. ADR-0006 correlation semantics are not changed by this task.

## Scope and exclusions

Included: retrieval through the existing `RedisPartialStateStore`, `SMEMBERS`
access, deserialization into `ClassifiedFragment`, explicit malformed-member
failures, and unit/integration tests.

Excluded: TTL, metrics, consolidation, PostgreSQL, API/frontend behavior, Kafka
acknowledgement, orchestration changes, fuzzy matching, conflict resolution, and
any universal or final person identifier.

## Retrieval contract

```python
retrieve_fragments(
    component_identifier: str,
) -> tuple[ClassifiedFragment, ...]
```

The adapter reuses `build_partial_state_key` and calls `SMEMBERS`. A missing key
returns `()`. All valid members are returned, including conflicting and incomplete
fragments. Set order is unspecified and is not part of the contract. Retrieval does
not delete, expire, overwrite, or otherwise mutate Redis state.

## Malformed-data and error behavior

Invalid JSON, a non-object JSON value, missing or extra fields, or incorrect field
types raises `MalformedFragmentError`, a `ValueError` subclass. Corrupt members are
never silently discarded. Redis exceptions from `SMEMBERS` propagate unchanged;
retry and operational handling remain outside this adapter.

## Acceptance criteria

- [ ] One stored fragment can be retrieved with all three fields preserved.
- [ ] Multiple fragments, including conflicts and incomplete valid payloads, are all
  returned without resolution.
- [ ] A missing key returns an empty tuple.
- [ ] Malformed JSON and structurally invalid members raise `MalformedFragmentError`.
- [ ] Redis retrieval errors propagate unchanged.
- [ ] Retrieval uses the existing key builder and validates the component identifier.
- [ ] Retrieval performs no mutation, deletion, or TTL operation.
- [ ] Unit and Redis integration tests cover the approved behavior.

## Testing

Unit tests use the injected fake Redis client for one fragment, multiple/conflicting
fragments, missing keys, malformed JSON, missing/extra fields, wrong field types,
Redis failure propagation, read-only behavior, and identifier validation.

Integration tests use the existing Redis fixture for store/retrieve, multiple
fragments, missing components, malformed members inserted directly, and Set
immutability after retrieval.

## Rollback

Rollback is removal or revert of the HRP-75 retrieval method, deserializer, tests,
and this specification. Existing HRP-74 stored data and write behavior remain
compatible because the key pattern, Set structure, member schema, and fragment
contract are unchanged.

## Accessibility and sustainability applicability

- Accessibility: not applicable — this is an internal backend storage capability
  with no user-facing flow.
- Sustainability: applicable through read-only bounded retrieval, preservation of
  Set deduplication, and avoidance of duplicate state or unnecessary writes. No
  carbon, energy, or retention claim is made.
- Deferred claims: TTL and retention evidence belong to HRP-76.
