# HRP-65 — Add safe Kafka consumer logging

**Integration status (2026-09-08):** Task changes integrated in develop; acceptance criteria not re-executed here.
**Git evidence:** [cdefded](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/cdefded) / [PR #23](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/23) (2026-08-31).
**Closeout interpretation:** See current architecture, runbook and test harness for subsequent changes and runtime limits.

This integration record does not assert current Jira status, reviewer approval identity
or a new passing test run. [Current documentation](../README.md) and
[acceptance/evidence matrix](../delivery-evidence.md) define the closeout reading.

## Historical specification and task evidence

The scope, criteria, checkboxes and test results below are the task's original record.
They are not a live progress dashboard. Pending-review/merge references in this
historical record are superseded by the integration evidence above; unresolved
functional limitations are not automatically marked as passed.

**Original recorded status:** Ready for review

**Owner:** Miguel
**Jira:** HRP-65
**Dependencies:** HRP-30 and HRP-31 consumer implementation already integrated in `develop`
**Related ADR:** None

## Objective

Provide verifiable, technical-only operational logging for the Kafka consumer without
recording Kafka payloads, message keys, personal data, secrets, or business semantics.

## Context and scope

- Includes: auditing the existing consumer logging, documenting its safe boundaries,
  and adding unit-test evidence that payload contents are absent from logs.
- Excludes: structured JSON logging, metrics, Prometheus, persistence logs, retry
  policy changes, data classification, payload validation, Docker, databases and ETL.
- Verified assumptions: the consumer is configured from authorised environment
  variables; topic names remain configuration rather than business classification.
- Risks: technical metadata such as topic, partition and offset is useful for
  operations but must not be combined with payload content in project logs.

## Design

`src/hr_pro_platform/ingestion/consumer.py` already uses the shared logger to report:

- consumer startup through the CLI entry point;
- subscribed topic count, not the configured topic list;
- received-message topic, partition, offset and byte size;
- missing message values and Kafka or polling error types;
- shutdown and the processed-message count.

The consumer does not decode, interpolate or pass message values to logging calls.
HRP-65 does not alter that implementation. It adds mock-based unit tests using a
synthetic sentinel payload to prove that log output retains technical metadata while
excluding the payload value.

## Acceptance criteria

- [x] Consumer logs startup/shutdown, topic count, safe message metadata and safe
  technical error information where those events occur.
- [x] Received-message logs include topic, partition, offset and byte size, but not
  a message body or key.
- [x] Tests prove a synthetic payload sentinel is absent from message and invalid-
  message log output.
- [x] No generator source, real Kafka payload, secret or environment file is used.
- [x] No metrics, persistence, Docker, ETL or retry-policy claim is added.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Unit | Consume one synthetic message | Metadata and processed count are logged; sentinel payload is absent |
| Unit | Handle a synthetic missing-value message | Safe error reason is logged; later sentinel payload remains absent |
| CI | Run the repository quality harness on Ubuntu | Lint, type, test and pre-commit evidence on the PR |

## Completion evidence

- Branch / PR: `feature/HRP-65-kafka-consumer-logging` / pending human review
- Commit: pending
- Commands and result: pending local and GitHub Actions execution
- Jira closing comment: pending merge and human verification
