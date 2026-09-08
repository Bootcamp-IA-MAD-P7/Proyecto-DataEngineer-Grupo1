# HRP-78 — Measure ingestion processing duration

**Integration status (2026-09-08):** Task changes integrated in develop; acceptance criteria not re-executed here.
**Git evidence:** [40e74b3](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/40e74b3) / [PR #73](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/73) (2026-09-07).
**Closeout interpretation:** Duration of ingestion processing is measured, not a whole Mongo-to-SQL ETL latency. Current histograms have no finite buckets for useful p95/p99.

This integration record does not assert current Jira status, reviewer approval identity
or a new passing test run. [Current documentation](../README.md) and
[acceptance/evidence matrix](../delivery-evidence.md) define the closeout reading.

## Historical specification and task evidence

The scope, criteria, checkboxes and test results below are the task's original record.
They are not a live progress dashboard. Pending-review/merge references in this
historical record are superseded by the integration evidence above; unresolved
functional limitations are not automatically marked as passed.

**Original recorded status:** In progress

**Owner:** Gabriela Granja
**Jira:** HRP-78
**Dependencies:** HRP-77; HRP-30/31 Kafka consumer; HRP-65 safe consumer logging; HRP-68 consumer unit tests
**Related ADR:** None

## Objective

Record the duration of ingestion processing for each successfully fetched,
non-Kafka-error message, using a timer-style metric that a later task can expose
to Prometheus without changing ingestion behaviour.

## Context and scope

- Includes: one process-local histogram/timer primitive, one observation per
  applicable message, and focused unit tests.
- Excludes: Kafka fetch latency, Mongo persistence duration, commit duration,
  rolling statistics, dashboards, exporters, HTTP/Prometheus exposition,
  monitoring infrastructure, and changes to HRP-77 semantics.
- Assumption: the current consumer's processing stage is the per-message
  decode/type-validation and routing decision before the `persist_*` calls.
- Risk: the process-local histogram resets on worker restart until a later
  exposition task provides external visibility.

## Semantic timing boundary

For every fetched record for which `msg.error()` is false, timing starts
immediately before the message's decoding and validation/routing work in the
consumer loop and stops immediately after that work has selected either a valid
`raw_events` entry or an invalid-event persistence route. The observation is
recorded in a `finally` block so exceptions still produce exactly one duration
for the attempted processing stage.

The boundary excludes `Consumer.consume()`, Kafka error handling, all Mongo
`persist_invalid_event` and `persist_batch` calls, `_durable_prefix_messages`,
Kafka commits, polling, shutdown and client setup/teardown. Invalid payloads are
applicable messages and are timed through their validation/routing decision;
Kafka error records are not applicable. Persistence remains a separate stage
for HRP-79.

## Design

`src/hr_pro_platform/observability/metrics.py` provides a dependency-free
`Histogram` with a deterministic metric name and a count/sum suitable for later
Prometheus exposition. It has no labels. The consumer accepts an optional
histogram for testability and otherwise uses the process-local default.

The consumer uses `time.perf_counter()` and observes seconds once per applicable
message after processing-stage execution. The metric stores non-negative finite
durations and does not retain payloads, identifiers or correlation keys.

## Metric semantics

- **Name:** `hr_pro_platform_ingestion_processing_duration_seconds`
- **Type:** histogram/timer-style metric
- **Unit:** seconds
- **Boundary:** per-message decode, validation and routing before persistence
- **Observation cardinality:** exactly once per fetched non-Kafka-error message
- **Labels:** none

## Acceptance criteria

- [x] Processing duration is recorded for each applicable message.
- [x] Each applicable message records exactly one observation.
- [x] The metric is independent of persistence duration and no HRP-79 metric is added.
- [x] Successful processing, error handling, commits and persistence behaviour remain unchanged.
- [x] No Prometheus exposition, exporter, dashboard, rolling statistic or monitoring infrastructure is added.
- [x] No high-cardinality labels or message/person/payload/correlation data are retained.
- [x] Targeted tests and repository quality checks provide reproducible evidence.

## Accessibility and sustainability applicability

- Accessibility: not applicable — this task adds no user-facing interface, API
  response or visual flow.
- Sustainability: applicable in a limited operational sense — one bounded
  process-local observation per processed message provides timing data without
  polling threads, payload retention or duplicate processing.
- Deferred claims: no Prometheus availability, production latency, carbon,
  energy or deployment claim is made by this task.

## Test strategy

| Level | Case | Evidence expected |
|---|---|---|
| Unit | Valid and invalid applicable messages | One non-negative processing observation per message |
| Unit | Persistence path | Persistence mocks remain outside the timed stage and existing successful behaviour is unchanged |
| Unit | Processing exception | One observation is recorded and existing exception handling continues |
| Quality | Static checks and spec validator | Repository commands complete with recorded results |

## Closing evidence

- Branch / PR: `feature/HRP-78-measure-processing-time` / PR #73.
- Commit: `4130bbb` (implementation commit).
- Commands executed and result:
  - `python scripts/validate_specs.py` — passed, 53 specifications validated.
  - `ruff check .` — blocked by access-denied warnings for existing temporary
    directories and one import-order finding; the finding was corrected and
    narrow changed-file Ruff validation passed.
  - `ruff format --check .` — blocked by Ruff crash while traversing existing
    inaccessible temporary directories; narrow changed-file format validation
    passed, 3 files already formatted.
  - `mypy src` — passed, no issues in 35 source files.
  - `pytest tests/unit/test_consumer_unit_coverage.py --no-cov` — passed, 8 tests.
  - `pytest --basetemp .pytest-tmp-hrp78` — passed, 262 passed and 40 skipped;
    two deprecation warnings were emitted.
  - `docker compose -f infra/compose.dev.yml config --quiet` — passed; Docker
    emitted access-denied warnings while reading its existing user config.
  - `pre-commit run --all-files` — blocked before hooks by the known
    `sqlite3.OperationalError: attempt to write a readonly database` and a
    permission error writing the pre-commit log.
- GitHub Actions `quality` — passed for PR #73.
- Jira closing comment: pending human review, merge and final evidence.
