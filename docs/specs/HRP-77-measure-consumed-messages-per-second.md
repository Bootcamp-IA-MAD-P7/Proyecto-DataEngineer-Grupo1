# HRP-77 — Measure consumed messages per second

**Integration status (2026-09-08):** Task changes integrated in develop; acceptance criteria not re-executed here.
**Git evidence:** [201e6e2](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/201e6e2) / [PR #72](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/72) (2026-09-07).
**Closeout interpretation:** A consumed-message counter is implemented; no sustained-throughput benchmark is established.

This integration record does not assert current Jira status, reviewer approval identity
or a new passing test run. [Current documentation](../README.md) and
[acceptance/evidence matrix](../delivery-evidence.md) define the closeout reading.

## Historical specification and task evidence

The scope, criteria, checkboxes and test results below are the task's original record.
They are not a live progress dashboard. Pending-review/merge references in this
historical record are superseded by the integration evidence above; unresolved
functional limitations are not automatically marked as passed.

**Original recorded status:** Ready for review

**Owner:** Gabriela Granja
**Jira:** HRP-77
**Dependencies:** HRP-30/31 Kafka consumer; HRP-65 safe consumer logging; HRP-68 consumer unit tests
**Related ADR:** None

## Objective

Provide a monotonic application counter for messages successfully returned by the
Kafka consumer so a later monitoring task can derive consumed messages per second
without changing ingestion behaviour.

## Context and scope

- Includes: a small in-process counter abstraction, one increment at the Kafka
  consumer boundary, and focused unit tests.
- Excludes: rolling-rate calculation, timers, background sampling, Prometheus
  exposition, HTTP endpoints, processing-duration metrics, persistence-duration
  metrics, dashboards, labels containing message or person identifiers, and
  changes to Kafka acknowledgement or persistence behaviour.
- Assumptions: `Consumer.consume()` returns a batch of Kafka records; records with
  a Kafka error are not successfully consumed messages for this metric.
- Risks: the counter is process-local and resets on worker restart until a later
  observability task provides an external exposition mechanism.

## Design

`src/hr_pro_platform/observability/metrics.py` provides a dependency-free
`MonotonicCounter` with the deterministic metric name
`hr_pro_platform_ingestion_messages_consumed_total`. The consumer accepts an
optional counter for testability and otherwise uses the process-local default.

For each record returned by `Consumer.consume()`, the consumer increments the
counter exactly once after confirming `msg.error()` is false and before checking
topic/coordinate validity, decoding, persistence or commit. Therefore malformed
records that were fetched from Kafka are still counted, while Kafka error records
and polling failures are not. The counter is independent of persistence outcomes,
retries and commits.

No metric labels are used. The counter is not exposed externally by HRP-77; that
belongs to HRP-80.

## Metric semantics

- **Name:** `hr_pro_platform_ingestion_messages_consumed_total`
- **Type:** monotonic counter
- **Unit:** messages
- **Boundary:** successful Kafka record fetch (`msg.error()` is false)
- **Increment cardinality:** exactly once per fetched record in the consumer path
- **Rate calculation:** deferred to an external monitoring system and HRP-80
- **Labels:** none

## Acceptance criteria

- [x] One successfully fetched Kafka record increments the counter exactly once.
- [x] Multiple successfully fetched records increment the counter once each.
- [x] Kafka error records and polling failures do not increment the counter.
- [x] Invalid payloads are counted at the fetch boundary without changing their
      existing persistence and commit behaviour.
- [x] The counter has no high-cardinality labels and does not log or retain payloads.
- [x] No Prometheus endpoint, processing-time metric, persistence-time metric or
      unrelated ingestion behaviour is added.
- [x] Targeted tests, specification validation and the applicable quality checks
      provide reproducible evidence; GitHub Actions `quality` is green/passing
      for PR #72, with the local pre-commit limitation recorded below.

## Accessibility and sustainability applicability

- Accessibility: not applicable — this task adds no user-facing interface, API
  response or visual flow.
- Sustainability: applicable in a limited operational sense — a monotonic counter
  avoids application-side timers, polling threads and repeated payload storage;
  the process-local value has bounded memory usage.
- Deferred claims: no Prometheus availability, production throughput, carbon,
  energy or deployment claim is made by this task.

## Test strategy

| Level | Case | Evidence expected |
|---|---|---|
| Unit | One fetched valid record | Counter value increases from 0 to 1 and existing persistence/commit path remains intact |
| Unit | Several fetched records | Counter value equals the number of non-error records |
| Unit | Kafka error record / polling failure | Counter does not increase for the error path and the consumer remains governed by existing handling |
| Unit | Invalid payload | Counter increases once while existing invalid-event persistence and commit assertions remain true |
| Quality | Static checks and spec validator | Repository commands complete with recorded results |

## Operational considerations

The counter is intentionally process-local and monotonic. It must not be used as a
rate directly or interpreted as durable history across restarts. HRP-80 may expose
this value to Prometheus and let Prometheus derive a rate. The counter contains no
payload, person identifier, topic label or other unbounded state.

## Closing evidence

- Branch / PR: `feature/HRP-77-measure-consumed-messages-per-second` / PR #72.
- Commit: `ae63da7` (implementation and tests); this evidence-closure update is
  the follow-up documentation commit.
- Commands executed and result:
  - `python scripts/validate_specs.py` — passed, 52 specifications validated.
  - `ruff check src/hr_pro_platform/observability/metrics.py
    src/hr_pro_platform/ingestion/consumer.py
    tests/unit/test_consumer_unit_coverage.py` — passed.
  - `ruff format --check src/hr_pro_platform/observability/metrics.py
    src/hr_pro_platform/ingestion/consumer.py
    tests/unit/test_consumer_unit_coverage.py` — passed.
  - `mypy src` — passed, no issues in 35 source files.
  - `pytest tests/unit/test_consumer_unit_coverage.py --no-cov` — passed, 6 tests.
  - `ruff check .` — passed with access-denied warnings for existing temporary
    pre-commit directories.
  - `ruff format --check .` — blocked by Ruff crash while traversing existing
    inaccessible temporary directories; `ruff format --check src tests scripts`
    passed, 79 files already formatted.
  - `pytest --basetemp .pytest-tmp-hrp77` — passed, 260 passed and 40 skipped;
    skips are existing unavailable-service checks and two deprecation warnings
    were emitted.
  - `docker compose -f infra/compose.dev.yml config --quiet` — passed; Docker
    emitted access-denied warnings while reading its existing user config.
  - `pre-commit run --all-files` — blocked before hooks by
    `sqlite3.OperationalError: attempt to write a readonly database` and a
    permission error writing `C:\Users\ggran\.cache\pre-commit\pre-commit.log`.
- Local/manual evidence: focused fake-consumer tests prove the fetch boundary,
  exact-once increments, invalid-message counting and unchanged commit behavior.
- CI evidence: GitHub Actions `quality` is green/passing for PR #72.
- Jira closing comment: pending human review, merge and final evidence.
