# HRP-67 — Add safe database logging

**Status:** Ready for review
**Owner:** Miguel
**Jira:** HRP-67
**Dependencies:** HRP-34, HRP-56 and HRP-57 database persistence boundaries
**Related ADR:** None

## Objective

Harden MongoDB and PostgreSQL database logging so persistence failures remain
operationally useful without exposing raw documents, SQL parameters, payload values,
secrets or personal data.

## Context and scope

- Includes: documenting the database logging contract, removing unsafe MongoDB bulk
  error detail logging, removing unbounded stack-trace logging from MongoDB insert
  failures, and adding regression tests for sensitive synthetic values in error paths.
- Excludes: Kafka consumer logic, ETL behaviour, MongoDB persistence semantics,
  PostgreSQL schema, PostgreSQL transaction policy, Redis, Prometheus, API, frontend,
  Docker and generator access.
- Verified assumptions: PostgreSQL component-insert failure logging already emits only
  `error_class` and `sqlstate`, without raw exception messages or SQL parameters.
- Risks: database driver error objects can include rejected document details or error
  messages that echo payload values, so logs must not serialize raw driver details.

## Design

MongoDB `insert_many_fragments()` keeps its existing control flow and return values:

- duplicate key bulk errors are still treated as expected replay/idempotency outcomes;
- non-duplicate bulk write errors still return `False`;
- generic insert failures still return `False`.

Only logging changes. Non-duplicate bulk write errors now log a bounded technical
summary containing an operation, status, technical error type and count. Generic insert
failures now log only the exception class name as a technical error type. The raw
`BulkWriteError.details`, exception message and stack trace are not emitted.

PostgreSQL logging is documented but not changed in this task because the inspected
error path already follows the approved pattern: it logs the operation outcome,
`error_class` and `sqlstate` after rollback without logging raw SQL parameters or
exception details.

## Acceptance criteria

- [x] MongoDB non-duplicate bulk write errors are logged without serializing raw
  `writeErrors` details.
- [x] MongoDB generic insert failures are logged without `exc_info=True` or raw
  exception messages.
- [x] Sensitive synthetic values embedded in MongoDB driver error details do not appear
  in logs.
- [x] Sensitive synthetic values embedded in generic exception messages do not appear
  in logs.
- [x] PostgreSQL error logging remains bounded to technical metadata; no functional
  PostgreSQL change is introduced.
- [x] No persistence semantics, schema, Kafka, ETL, Redis, Prometheus, API, frontend,
  Docker or generator scope is changed.

## Accessibility and sustainability applicability

- Accessibility: not applicable — HRP-67 introduces no user-facing interface, visual
  output, API response or interactive flow.
- Sustainability: applicable in a limited operational sense — bounded logging avoids
  duplicating raw payload storage in log streams and reduces noisy diagnostic output.
- Deferred claims: no Prometheus, dashboard, carbon, energy, AWS or formal
  observability claim is made by this task.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Unit | MongoDB bulk write error details contain a sensitive sentinel | The operation fails safely and the sentinel/raw `writeErrors` are absent from logs |
| Unit | MongoDB generic exception message contains a sensitive sentinel | The operation fails safely and the sentinel/raw traceback are absent from logs |
| Unit | Existing PostgreSQL failure logging | Existing tests continue proving `error_class`/`sqlstate` only |
| CI | Repository quality harness | Ruff, format, mypy, pytest and spec validation pass |

## Completion evidence

- Branch / PR: `feature/HRP-67-database-logging` / pending human review
- Commit: `3361d77`
- Commands and result: `python scripts/validate_specs.py`,
  `ruff check src/hr_pro_platform/ingestion/mongo.py tests/unit/test_kafka_consumer.py
  docs/specs/HRP-67-database-logging.md`, `ruff format --check
  src/hr_pro_platform/ingestion/mongo.py tests/unit/test_kafka_consumer.py`,
  `mypy src`, `pytest tests/unit/test_kafka_consumer.py -k hrp67 --no-cov` and
  `pytest tests/unit/test_person_repository.py --no-cov` passed locally.
  The broader local `tests/unit/test_kafka_consumer.py` run is limited by Windows
  Application Control blocking the Confluent Kafka DLL in existing consumer tests;
  GitHub Actions must provide authoritative full-suite evidence.
- Jira closing comment: pending merge and human verification
