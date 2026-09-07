# HRP-79 — Measure ingestion persistence duration

**Status:** In progress  
**Owner:** Gabriela Granja  
**Jira:** HRP-79  
**Branch:** `feature/HRP-79-measure-persistence-time`  
**PR:** pending  
**Implementation commit:** pending  
**Dependencies:** HRP-77, merged HRP-78, HRP-30/31 Kafka consumer, HRP-68 consumer tests  
**Related ADR:** None

## Objective

Record the duration of each MongoDB raw-event persistence attempt during ingestion,
without changing persistence, Kafka commit, exception, or existing observability
semantics.

## Context and scope

- Includes: one process-local histogram, one observation per call to the Mongo
  persistence boundary, deterministic unit tests, and traceable documentation.
- Excludes: Kafka fetch/wait time, message decoding and routing measured by HRP-78,
  Kafka commit, consumer lifecycle, Prometheus exposition/configuration, dashboards,
  retries, and HRP-80.
- The HRP-78 merge precondition is verified by ancestry from
  `40e74b37ba8e205596a45c79fef4442edbf621ba`.
- Accessibility is not applicable: this change has no user-facing interface or API.
- Sustainability is applicable in a limited operational sense: the metric is a
  bounded process-local observation with no polling, payload retention, or duplicate
  processing. No energy or carbon claim is made.

## Persistence boundary discovered from implementation

The applicable persistence operation is `MongoIngestionClient._persist`, called by
both `persist_raw_event` and `persist_invalid_event` (including calls made through
`persist_batch`). It performs the opposite-collection conflict lookup, the target
collection idempotency lookup, and `insert_one` when a new document is required.

- **Start:** immediately on entry to `_persist`, before coordinate construction and
  MongoDB lookups.
- **End:** on exit from `_persist`, including every returned status and the caught
  failure paths.
- **Commit:** Kafka `consumer.commit` is excluded. MongoDB has no separate commit
  operation in this adapter; the boundary ends after the MongoDB operation returns.
- **Successful attempts:** one duration is observed for `inserted`,
  `already_exists`, and `unresolved_conflict` outcomes.
- **Failed attempts:** one duration is observed for the existing `failed` outcome,
  including missing collections and exceptions caught by the existing persistence
  handler. Existing exceptions remain converted to the same `failed` outcome and
  are not rethrown or swallowed differently.
- **Multiple paths:** valid and invalid raw-event persistence share `_persist`, so
  both paths use the same truthful boundary and metric. No aggregate batch timing is
  recorded; `persist_batch` produces one observation per event call.

## Design and metric semantics

`src/hr_pro_platform/observability/metrics.py` provides the dependency-free,
process-local `Histogram`. `MongoIngestionClient` accepts an optional histogram for
deterministic tests and otherwise creates the default timer. `time.perf_counter()`
provides monotonic elapsed time and a `finally` block records exactly once per
`_persist` invocation.

- **Name:** `hr_pro_platform_ingestion_persistence_duration_seconds`
- **Type:** histogram/timer-style metric
- **Unit:** seconds
- **Labels:** none
- **Cardinality policy:** no labels, IDs, payload values, correlation identifiers,
  exception messages, or sensitive data are retained.
- **Reset behavior:** process-local count and sum reset when the worker process
  restarts; external exposition is deferred to a later task.

HRP-78 remains responsible for the pre-persistence decode, validation, and routing
duration under `hr_pro_platform_ingestion_processing_duration_seconds`. HRP-79 does
not alter that metric or the HRP-77 consumed-message counter.

## Acceptance criteria

- [x] Persistence duration metric exists.
- [x] Exact persistence timing boundary is documented.
- [x] Exactly one observation is recorded per applicable persistence attempt.
- [x] Successful persistence behavior is preserved.
- [x] Failure/exception semantics are preserved.
- [x] Commit semantics are preserved.
- [x] HRP-77 semantics remain unchanged.
- [x] HRP-78 processing-duration semantics remain unchanged.
- [x] No high-cardinality or sensitive data is introduced.
- [x] Focused deterministic tests cover the metric.
- [x] HRP-80 remains out of scope.
- [x] SDD evidence matches implementation and validation.

## In-scope and out-of-scope decisions

The change is limited to the metric constant, the existing Mongo persistence adapter,
focused tests, and this spec. It does not add an endpoint, exporter, Prometheus
configuration, dashboard, retry, transaction change, data change, or unrelated
refactor. Rollback is deleting the HRP-79 commits; the prior persistence path remains
available without the metric.

## Test strategy

| Level | Case | Evidence expected |
|---|---|---|
| Unit | Two valid raw events through `persist_batch` | Two observations with deterministic elapsed time |
| Unit | Existing persistence failure | One observation and unchanged `failed` outcome |
| Unit | Existing idempotent duplicate path | One observation and unchanged `already_exists` outcome |
| Quality | Repository validation and focused/full pytest | Reproducible command results |

## Closing evidence

- **Branch / PR:** `feature/HRP-79-measure-persistence-time` / pending (no PR has been created yet).
- **Implementation commit:** pending until the implementation commit exists.
- **Local validation:** `python scripts/validate_specs.py` passed (54 specs); `ruff check .`
  passed; `ruff format --check .` passed (224 files); `mypy src` passed (35 source
  files); targeted HRP-79 plus HRP-78/77 consumer tests passed (11 tests); full
  `pytest --basetemp .pytest-tmp-hrp79` passed (265 passed, 40 skipped, 2 warnings);
  Compose config passed; `git diff --check` passed.
- **CI:** pending until a PR exists and GitHub Actions reports its state.
- **Pre-commit:** BLOCKED by the local environment before hooks: SQLite readonly
  database and permission denied writing `C:\Users\ggran\.cache\pre-commit\pre-commit.log`.
- **Environment limitations:** integration tests skipped because MongoDB/PostgreSQL/
  Redis services were unavailable; Docker emitted access-denied warnings for its user
  config; these are not product failures.
- **Jira closing comment:** pending human review, merge, and final evidence.
