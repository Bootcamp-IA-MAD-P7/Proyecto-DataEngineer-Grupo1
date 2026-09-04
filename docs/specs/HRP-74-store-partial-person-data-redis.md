# HRP-74 — Store partial person data in Redis

**Status:** Implemented — pending merge
**Jira:** HRP-74
**Owner:** Gabriela Granja
**Pull request:** [#66](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/66)
**Implementation commit:** `c1140fb`
**Dependencies:** HRP-73, HRP-50, HRP-51, ADR-0005 and ADR-0006
**Related ADRs:** [ADR-0005](../adr/0005-kafka-acknowledgement-after-raw-persistence.md), [ADR-0006](../adr/0006-person-correlation-key.md)

## Objective

Store validated and classified person fragments as temporary, provenance-bearing
correlation state in Redis. HRP-74 does not store a final consolidated person record
and does not introduce a universal `person_id`.

## Scope and boundaries

Included:

- the synchronous `redis-py` client dependency;
- an injected Redis storage adapter;
- canonical serialization of classified fragments;
- accumulation in a Redis Set;
- exact-duplicate idempotency;
- preservation of conflicting and incomplete evidence;
- unit tests and focused Redis integration tests.

Excluded:

- Redis retrieval for ETL (HRP-75);
- TTL or expiration (HRP-76);
- monitoring and Prometheus (HRP-77 through HRP-80);
- final consolidated records, PostgreSQL, API and frontend behavior;
- Kafka acknowledgement changes;
- creation of a new process-worker architecture.

The repository has no production process-worker call site yet. This task therefore
implements the reusable storage contract without inventing a larger orchestration
layer. A future processing stage supplies the already-derived provisional component
identifier.

## Approved correlation boundary

The identifier passed to the adapter is an opaque provisional operational component
identifier created by the approved correlation stage. It is not a universal or final
`person_id`.

The approved exact correlation edges remain:

- Personal `passport` ↔ Bank `passport`;
- Personal `name + " " + last_name` ↔ Location `fullname`;
- Location `fullname` ↔ Professional `fullname`;
- Location `address` ↔ Net `address`.

The storage adapter does not perform correlation, normalization, fuzzy matching,
fallback matching or conflict resolution.

## Redis storage contract

**REDIS KEY PATTERN:** `hrp:partial:{provisional_component_identifier}`

The component identifier is passed opaquely by the correlation stage. The adapter
does not call it `person_id`, derive a business identity, or log it.

**VALUE/ENTRY FORMAT:** one classified fragment encoded as a JSON object containing
`classification`, `payload` and `source_reference`.

**SERIALIZATION:** JSON with sorted object keys, compact separators and stable scalar
representation. `ensure_ascii=True` is used for deterministic byte representation.

**STRUCTURE:** Redis Set.

**ACCUMULATION:** `SADD` adds each canonical fragment entry to the component Set.
Existing evidence is retained.

**DUPLICATE BEHAVIOR:** an identical `(classification, payload, source_reference)`
entry is naturally idempotent because Redis Set membership is unique.

**CONFLICT BEHAVIOR:** different classified fragments or different source references
are separate Set entries. No value is overwritten and no conflict is resolved.

**ATOMICITY:** one `SADD` command is sufficient. HRP-74 does not perform a
read-modify-write merge and therefore does not require `WATCH/MULTI` or Lua.

**FAILURE BEHAVIOR:** Redis errors are surfaced by the adapter. The existing
processing layer owns safe logging and retry decisions. MongoDB RAW persistence
remains the durable Kafka acknowledgement boundary under ADR-0005.

**TTL:** OUT OF SCOPE FOR HRP-74; owned by HRP-76.

## Acceptance criteria

- [x] A classified fragment is stored under the supplied provisional component key.
- [x] Classification, payload and source reference are preserved.
- [x] A second fragment for the same component is accumulated.
- [x] Repeating the exact same fragment does not add a second Set entry.
- [x] Conflicting fragments remain separately visible in the Set.
- [x] Incomplete but valid fragments are preserved.
- [x] Serialization is deterministic.
- [x] Redis failures are surfaced without exposing payloads or keys in adapter logs.
- [x] No TTL command is issued.
- [x] No consolidated record or retrieval API is implemented.
- [x] Kafka acknowledgement semantics remain unchanged.

## Testing

Unit tests use an injected fake Redis client and cover key construction, canonical
serialization, accumulation, duplicates, conflicts, incomplete fragments and
failure propagation. Integration tests use the HRP-73 Redis container and inspect
Redis directly from the test only; they do not introduce production retrieval.

## Accessibility and sustainability applicability

- Accessibility: not applicable — this is an internal backend storage capability.
- Sustainability: applicable through bounded temporary storage, exact-duplicate
  idempotency and no duplicate raw-event storage. No carbon or energy claim is made.
- Deferred claims: TTL policy and retention evidence belong to HRP-76.

## Evidence and rollback

Validation evidence for PR #66 includes the focused unit suite, the Redis-backed
integration suite against real Redis, Compose validation, lint, format, type checks
and the full test suite. Current CI check results are maintained by PR #66 and are
the source of truth at review time; transient local test counts are not duplicated
here. The focused Redis run's repository-wide coverage warning is expected when
only one test is selected. Rollback is removal of the HRP-74 adapter and dependency;
MongoDB RAW remains independently recoverable.
