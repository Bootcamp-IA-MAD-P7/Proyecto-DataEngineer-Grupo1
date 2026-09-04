# HRP-66 — Add ETL processing logs

**Status:** Ready for review
**Owner:** Miguel
**Jira:** HRP-66
**Dependencies:** HRP-43, HRP-44, HRP-45, HRP-46, HRP-47, HRP-48, HRP-49 and HRP-50
provide the transformation stages that can use this logging helper.
**Related ADR:** None

## Objective

Provide a small, reusable and safe logging boundary for ETL processing stages so the
project can report transformation progress without exposing payloads, secrets or
personal data.

## Context and scope

- Includes: a technical-only ETL log-event builder, a logger helper, unit tests and
  observability documentation alignment.
- Excludes: Kafka consumer changes, MongoDB raw persistence, PostgreSQL writes, Redis,
  Prometheus, dashboards, business validation, data cleaning, grouping rules, final
  person-record logic and generator access.
- Verified assumptions: transformation code already contains pure classification,
  validation, grouping and consolidation stages; logging must not make those stages
  depend on infrastructure.
- Risks: logging helpers can become a path for payload leakage if they accept raw
  objects; this task therefore exposes only bounded technical metadata.

## Design

The new `hr_pro_platform.observability.etl_logging` module provides two functions:

- `build_etl_log_event()` returns a structured dictionary with technical metadata
  such as component, event type, stage, status, domain, counts, error type and
  processing duration.
- `log_etl_event()` emits that event as a compact JSON string through an injected
  standard-library logger.

The interface deliberately does not accept payloads, Kafka keys, correlation values,
addresses, emails, IBANs, salaries, passports, phone numbers, environment values or
database records. This keeps logging reusable from ETL orchestration without coupling
the pure transformation modules to Docker, Kafka, MongoDB or PostgreSQL.

The textual metadata is bounded by controlled technical values:

| Field | Allowed values |
|---|---|
| `stage` | `classification`, `validation`, `grouping`, `consolidation`, `etl` |
| `status` | `started`, `completed`, `failed`, `skipped` |
| `domain` | `Personal`, `Location`, `Professional`, `Bank`, `Net`, `unknown` |
| `error_type` | `invalid_metadata`, `validation_error`, `classification_error`, `grouping_error`, `consolidation_error`, `unexpected_error` |

## Acceptance criteria

- [x] ETL processing logs can represent stage, status, optional domain, technical
  counts, error type and `processing_time_ms`.
- [x] The logging API does not accept raw payloads, secrets, PII or correlation values.
- [x] Logs are emitted as structured JSON through `stdout`-compatible Python logging.
- [x] Invalid technical metadata, such as uncontrolled textual metadata or negative
  counts, is rejected before logging.
- [x] Unit tests prove the event shape and absence of payload/PII fields.
- [x] No Kafka, MongoDB, PostgreSQL, Redis, API, frontend or generator scope is changed.

## Accessibility and sustainability applicability

- Accessibility: not applicable — HRP-66 introduces no user-facing interface, visual
  output, API response or interactive flow.
- Sustainability: applicable — bounded technical metadata reduces log volume and
  avoids duplicating sensitive payload storage in operational logs.
- Deferred claims: no carbon, energy, AWS, Prometheus or formal observability claim is
  made by this task.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Unit | Build an ETL log event | Deterministic technical metadata shape |
| Unit | Emit an ETL log event | JSON log excludes payload and PII field names |
| Unit | Invalid metadata | Uncontrolled text values and negative numeric values fail fast |
| CI | Repository quality harness | Ruff, format, mypy, pytest and spec validation pass |

## Completion evidence

- Branch / PR: `feature/HRP-66-etl-processing-logs` / PR #58
- Commits: `2ffb83a`, `0817c72`, `b428962`; latest fix pending
- Commands and result: `python scripts/validate_specs.py`, `ruff check .`,
  `ruff format --check .`, `mypy src` and `pytest tests/unit/test_etl_logging.py
  --no-cov` passed locally. Full local `pytest` is limited by Windows Application
  Control blocking the Confluent Kafka DLL in existing ingestion tests; GitHub Actions
  must provide the authoritative full-suite evidence.
- Jira closing comment: pending merge and human verification
