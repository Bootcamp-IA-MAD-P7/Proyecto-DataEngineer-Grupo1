# HRP-68 — Kafka consumer unit tests

**Status:** Ready for review
**Owner:** Miguel
**Jira:** HRP-68 — Crear tests unitarios del consumer
**Dependencies:** HRP-30 and HRP-31 consumer behaviour; HRP-34 raw MongoDB persistence boundary
**Related ADR:** None

## Objective

Strengthen the Kafka consumer unit-test coverage so the ingestion behaviour can be
reviewed without running Kafka, inspecting the educational generator or relying on
manual broker evidence.

## Context and scope

- Includes: task-level specification and focused unit tests around the existing
  consumer behaviour.
- Excludes: consumer feature changes, Kafka runtime execution, MongoDB/PostgreSQL
  services, ETL, Redis, API, frontend, Docker, data-contract changes and generator
  access.
- Verifiable assumptions: the current consumer reads its authorised topics from
  configuration, persists raw JSON objects through the Mongo ingestion boundary,
  persists technical invalid events separately, commits only durable offsets and
  closes external clients in `finally`.
- Risks: tests that only assert "a mock was called" can be misleading. HRP-68 tests
  must prove observable behaviour: subscription, durable commits, failed persistence
  not being committed, invalid-event routing and resource cleanup.

## Design

The tests use fake Kafka messages and a fake consumer injected with mocks. They do
not start Kafka, MongoDB or the educational runtime. Test payloads are synthetic and
minimal; no real observed values or personal data are used.

The implementation code remains unchanged unless a test exposes a consumer bug that
is directly within HRP-68 scope.

## Acceptance criteria

- [x] The consumer subscribes to the configured topic list, not to a hard-coded
  topic.
- [x] A valid JSON object is persisted through the raw MongoDB boundary and its
  offset is committed only after a durable persistence outcome.
- [x] A failed persistence outcome does not commit the Kafka offset.
- [x] Technical invalid payloads are routed through `persist_invalid_event()` and
  are committed only when that persistence outcome is durable.
- [x] Kafka and MongoDB clients are closed after the controlled test run.
- [x] No Kafka broker, MongoDB instance, PostgreSQL instance or educational
  generator is required for the unit tests.

## Accessibility and sustainability applicability

- Accessibility: not applicable — this task introduces no user-facing interface,
  API response or visual flow.
- Sustainability: applicable in a limited quality sense — fast unit tests reduce
  unnecessary external-service usage during normal development and CI.
- Deferred claims: no throughput, load, carbon, AWS or production reliability claim
  is made by this task.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Unit | Configured topic subscription | Fake consumer receives the patched topic list |
| Unit | Durable raw persistence | Valid message is persisted and committed |
| Unit | Failed raw persistence | Failed persistence returns no committed offset |
| Unit | Durable invalid-event persistence | Invalid payload is routed and committed |
| Unit | Cleanup | Kafka and MongoDB clients close in controlled runs |

## Completion evidence

- Branch / PR: `feature/HRP-68-kafka-consumer-unit-tests` / pending
- Commit: pending
- Commands executed and result:
  - `python scripts/validate_specs.py` — passed, 43 specs validated.
  - `ruff check tests/unit/test_consumer_unit_coverage.py
    src/hr_pro_platform/ingestion/consumer.py
    docs/specs/HRP-68-kafka-consumer-unit-tests.md` — passed.
  - `ruff format --check tests/unit/test_consumer_unit_coverage.py
    src/hr_pro_platform/ingestion/consumer.py` — passed.
  - `mypy src` — passed, no issues in 31 source files.
  - `pytest tests/unit/test_consumer_unit_coverage.py --no-cov` — blocked in this
    Windows environment because Application Control prevents importing
    `confluent_kafka.cimpl`; GitHub Actions on Ubuntu must provide authoritative
    execution evidence.
- Jira closing comment: pending review, merge and final evidence
