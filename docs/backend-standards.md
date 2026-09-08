---
description: Python data-platform standards for ingestion, ETL, persistence and serving.
alwaysApply: true
---

# Backend and data-platform standards

## Stack and module boundaries

The application is Python 3.11+ under `src/hr_pro_platform/`. Keep adapters at the
edge and orchestration independent of Kafka, MongoDB, Redis, PostgreSQL and HTTP
libraries where practical.

| Module | Responsibility | Must not do |
|---|---|---|
| `ingestion` | Consume, minimally validate and persist raw events | Perform business aggregation |
| `transformation` | Classify, correlate, validate and build canonical records | Serve HTTP |
| `storage` | Repository adapters and idempotent persistence | Contain business decisions |
| `api` | Read-only query endpoints and response validation | Access raw MongoDB data |
| `observability` | Technical logs and ingestion metrics; tracing is not implemented | Log sensitive payloads |

## Python rules

- Add type hints for public functions and data boundaries; run `mypy` for production
  code.
- Use `dataclass` or validated models for message boundaries rather than untyped
  dictionaries leaking throughout the application.
- External clients are injected or wrapped behind small interfaces so unit tests do
  not need live Kafka or databases.
- Handle failures according to the adapter contract: technical-only logs and no
  acknowledgement of unpersisted data. A failure metric is a design improvement,
  not a currently exposed metric; see [observability](06-observability.md).
- Configuration is read from environment variables and validated at startup. Never
  hard-code endpoints or secrets.

## Data correctness

- Raw-event idempotency is keyed by `topic + partition + offset`.
- Curated persistence follows its repository contract and technical source-reference
  idempotency. Operational correlation uses ADR-0006 exact edges; no global business
  key or passport/IBAN uniqueness may be inferred from the bounded observation.
- Redis data has a TTL and cannot be the sole source of truth.
- Schema changes require a spec update; contract/model boundary changes also require
  an ADR.

## Testing

- Start with a failing behaviour test where feasible.
- Unit tests mock Kafka and persistence adapters. Integration tests use Docker Compose
  only when the relevant service exists.
- Cover normal flow, malformed message, duplicate/replay, dependency failure and
  shutdown/recovery paths relevant to the change.
- Never use live educational payloads in tests.

## API additions

Before FastAPI implementation, update the API contract/spec. Include input validation,
pagination or filtering rules when applicable, safe errors and tests for success and
invalid requests.
