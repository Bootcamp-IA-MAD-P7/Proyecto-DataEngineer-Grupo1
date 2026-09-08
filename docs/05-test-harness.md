# Test harness and evidence

## Layers actually present

| Layer | Location | Boundary |
|---|---|---|
| Unit | tests/unit | Fakes, pure transformations, repositories, API and metrics |
| Integration | tests/integration | Real MongoDB/PostgreSQL or explicitly configured Redis |
| E2E synthetic | tests/e2e/test_kafka_mongodb_postgresql_flow.py | Synthetic Kafka-equivalent events, real MongoDB and PostgreSQL |
| Fixtures | tests/fixtures and inline test fixtures | Sanitized/synthetic values; no generator inspection |

There is no separate tests/contract directory or implemented load-test runner in this
checkout. Contract checks live in the unit suites. Unit tests still need installed
Python dependencies: “no external services” does not mean “no native dependencies”.

## Recorded local attempt

Code baseline f3a952b, 2026-09-08, Windows/Python 3.11:
246 passed + 21 failed + 40 skipped = 307 tests; calculated coverage 82.91%.
The threshold in pyproject.toml is 75%. This is a failed test run, not a green release.

An isolated import diagnosed a Windows Application Control block loading
confluent-kafka's cimpl extension. Secondary unittest.mock errors hid that ImportError.
MongoDB/PostgreSQL absence and missing HRP74_REDIS_URL caused integration skips.
This explains the observed environment but does not substitute for a successful
rerun or certify every failure independently.

## CI definition versus result

The supplied quality workflow runs on Ubuntu, installs .[dev], then checks specs,
pre-commit, Ruff, mypy, pytest and Compose syntax. It provisions PostgreSQL and MongoDB,
not Redis or a Kafka broker. A versioned workflow is evidence of configuration;
a claim that a run passed needs its specific run URL and commit.

## Commands

Run from the repository root:

```bash
python scripts/validate_specs.py
pre-commit run --all-files
ruff check .
ruff format --check .
mypy src
python -m pytest
docker compose -f infra/compose.dev.yml config --quiet
```

For a bounded unit run:
`python -m pytest tests/unit -q --no-cov`.
For collection without writing coverage:
`python -m pytest --collect-only -q --no-cov`.
Integration fixtures perform writes and cleanup; use only dedicated test databases,
as explained in the [runbook](07-runbook.md).

## What a check establishes

- Spec validation checks filename, Jira metadata, objective and checklist structure.
  It does not approve meaning, accuracy, links or implementation completeness.
- Coverage is executed-line coverage, not a percentage of accepted briefing checks.
- A healthcheck is availability, not data correctness.
- HRP-71 is not a live-broker throughput, restart or sustained-runtime benchmark.
- Documentation edits require consistency/link checks; no application rerun is
  implied when no code or runtime behaviour changes.

## Fixtures and future evidence

Retain only minimum structural evidence and synthetic values. Accessibility,
load, disaster recovery and public API security need their own applicable evidence;
a policy or architecture direction is not a measured result.

## Unverified operational boundaries

The consumer's durable-prefix helper evaluates one batch at a time; there is no
cross-batch unresolved-gap ledger. Per-batch tests do not establish that a later
commit cannot overtake an earlier unpersisted event. Generic consumer exception
logging also lacks a universal redaction filter. These code boundaries were identified
read-only; no regression fix or new functional test is claimed by this documentation.
