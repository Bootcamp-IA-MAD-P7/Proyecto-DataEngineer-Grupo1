# HRP-71 — Kafka to MongoDB to PostgreSQL E2E coverage

**Status:** Ready for review
**Owner:** Miguel
**Jira:** HRP-71 — Crear prueba completa Kafka → MongoDB → PostgreSQL
**Dependencies:** HRP-30/31 consumer behaviour, HRP-34 MongoDB raw boundary, HRP-50
person consolidation, HRP-55/56/57/58 PostgreSQL persistence and HRP-63 Compose
**Related ADR:** `docs/adr/0002-raw-and-curated-storage.md`,
`docs/adr/0005-kafka-acknowledgement-after-raw-persistence.md`,
`docs/adr/0006-person-correlation-key.md`

## Objective

Provide a reproducible end-to-end test that proves the implemented pipeline can move
Kafka-equivalent event evidence through MongoDB raw storage, transformation and
curated PostgreSQL persistence without using the educational generator or real
payload captures.

## Context and scope

- Includes: one focused E2E test using synthetic Kafka coordinates and payloads,
  real MongoDB raw persistence, existing transformation/consolidation functions,
  existing PostgreSQL mapping and repository code, and real PostgreSQL assertions.
- Excludes: starting or inspecting the educational Kafka generator, running a real
  Kafka broker, changing consumer logic, changing MongoDB persistence semantics,
  changing transformation rules, changing PostgreSQL schema/repository behaviour,
  Redis, API, frontend, Docker changes and performance claims.
- Verifiable assumptions: HRP-34 persists raw JSON payloads with actual technical
  coordinates; HRP-50 consolidates five approved domains through ADR-0006 exact
  edges; HRP-55/56 persist mapped records to PostgreSQL.
- Risks: this test proves the pipeline after Kafka delivery has provided a message
  and coordinates. It does not prove real broker throughput, consumer polling speed
  or the educational generator behaviour.

## Design

The test treats Kafka as the upstream transport boundary by creating five synthetic
events with explicit `topic`, `partition` and `offset` values. Those events are
persisted through `MongoIngestionClient.persist_raw_event()`, then read back from
MongoDB raw storage.

Each MongoDB raw document is classified and validated using the existing
transformation boundary, converted into `ClassifiedFragment`, grouped with the
existing domain groupers, consolidated with `consolidate_person_records()`, mapped
with `map_person_record()` and inserted with `PersonRepository.insert_mapping()`.

Assertions are made against both stores:

- MongoDB contains the five raw technical coordinates.
- PostgreSQL contains one curated employee plus rows for location, professional,
  bank and network data under the same `employee_id`.

All payload values are synthetic and intentionally minimal. The test never reads,
executes or infers the educational generator.

## Acceptance criteria

- [x] The test starts from Kafka-equivalent synthetic topic/partition/offset events.
- [x] The events are persisted through the real MongoDB raw boundary.
- [x] The raw MongoDB documents are read back before transformation.
- [x] The existing classification, validation, grouping, consolidation, mapping and
  PostgreSQL repository code is reused; no pipeline logic is duplicated in
  production code.
- [x] PostgreSQL is verified for one final curated person record and related domain
  rows.
- [x] No real Kafka broker, educational generator, payload capture, `.env`, secret or
  PII is required.
- [x] The test skips cleanly when local MongoDB/PostgreSQL services are not available.

## Accessibility and sustainability applicability

- Accessibility: not applicable — this is backend E2E validation with no
  user-facing flow, API response or visual interface.
- Sustainability: applicable in a limited delivery sense — the test reuses the
  existing Compose services and existing pipeline code, avoiding a duplicated stack
  or additional external dependency.
- Deferred claims: no Kafka throughput, live-generator compatibility, AWS,
  production reliability, carbon or energy claim is made by this task.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| E2E | Five Kafka-equivalent synthetic events persist to MongoDB raw storage and then to PostgreSQL curated tables | Real MongoDB and PostgreSQL services available through `infra/compose.dev.yml`; one complete person persisted and queryable |
| Static | Spec and changed test files remain valid | Spec validation, Ruff and mypy pass |
| CI/manual | Full repository harness | GitHub Actions or local Docker-backed run supplies authoritative full-suite evidence |

## Completion evidence

- Branch / PR: `feature/HRP-71-kafka-mongodb-postgresql-e2e-test` / pending
- Commit: pending
- Commands executed and result:
  - `docker compose -f infra/compose.dev.yml config --quiet` — passed.
  - `docker compose -f infra/compose.dev.yml up -d mongo postgres` — MongoDB and
    PostgreSQL started/running.
  - `docker compose -f infra/compose.dev.yml ps` — both services reported healthy.
  - `python scripts/validate_specs.py` — passed, 45 specs validated.
  - `ruff check tests/e2e/test_kafka_mongodb_postgresql_flow.py
    docs/specs/HRP-71-kafka-mongodb-postgresql-e2e-test.md` — passed.
  - `ruff format --check tests/e2e/test_kafka_mongodb_postgresql_flow.py` —
    passed.
  - `mypy src` — passed, no issues in 31 source files.
  - `pytest tests/e2e/test_kafka_mongodb_postgresql_flow.py --no-cov` — passed,
    1 test passed against real MongoDB and PostgreSQL.
  - Note: the E2E test pins local PostgreSQL to `127.0.0.1`, matching
    `infra/compose.dev.yml` port binding, to avoid host-resolution differences in
    local test environments.
- Jira closing comment: pending review, merge and final evidence
