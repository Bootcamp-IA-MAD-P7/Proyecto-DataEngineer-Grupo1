# HRP-22 — Evolve project quality, documentation and presentation evidence

**Status:** In progress
**Owner:** Miguel
**Jira:** HRP-22
**Dependencies:** HRP-23, HRP-24, HRP-29, HRP-30 and HRP-31 completed
**Related ADR:** `docs/adr/0005-kafka-acknowledgement-after-raw-persistence.md`

## Objective

Turn the current foundation into an accurate, presentation-ready project baseline by
strengthening automated quality, recording reusable architectural lessons, maintaining
an evidence-based SWOT analysis and replacing stale README claims with verifiable state.

## Context and scope

- Includes: an initial coverage gate, Docker Compose validation, a raw-persistence
  acknowledgement decision, an external benchmark, an evolving SWOT, the 2026-08-28
  daily and presentation sources, and a complete README revision.
- Excludes: copying third-party source code, implementing MongoDB persistence, fragment
  classification, ETL, Redis, PostgreSQL, API, frontend, Airflow or monitoring services.
- Verifiable assumptions: `develop` contains the reviewed Kafka consumer and evidence;
  the local MongoDB development service has already passed its health check.
- Risks: documentation may overstate target capabilities; a coverage gate may become a
  vanity metric unless it is paired with behaviour-focused tests.

## Design

The change uses the existing SDD and harness structure. External material is treated as
a benchmark, not a dependency or implementation source. Architectural lessons are
converted into project-owned decisions and acceptance tests. The README distinguishes
validated, active and planned capabilities.

The initial line-coverage floor is 75%. It is intentionally below the measured 79%
baseline and must ratchet upward as executable code grows. Docker Compose syntax is
validated in CI without starting services.

## Acceptance criteria

- [x] CI rejects coverage below 75% and an invalid development Compose file.
- [x] Kafka acknowledgement after raw persistence is documented as a reviewable ADR.
- [x] The benchmark identifies patterns to adopt and risks to avoid without copying code.
- [x] The SWOT has evidence, owners, review cadence and an evolution history.
- [x] The daily and NotebookLM sources contain only verified work and current risks.
- [x] The README clearly separates current capabilities from the target architecture.
- [x] Pre-commit, Ruff, formatting, mypy, pytest with coverage and spec validation pass.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Documentary | README, benchmark and SWOT review | No planned feature is presented as complete |
| Harness | Coverage below the threshold | CI command exits unsuccessfully |
| Infrastructure | Compose configuration | `docker compose ... config --quiet` passes |
| Regression | Existing Python behaviour | Current unit tests remain green |

## Completion evidence

- Branch / PR: `feature/HRP-22-project-evolution-readme` /
  [PR #15](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/15).
- Primary commit: `e96d841`.
- Commands and result: pre-commit, spec validation, Ruff lint/format, mypy, pytest and
  Compose configuration passed locally; 7 tests passed with 78.50% measured coverage.
- Jira closing comment: HRP-22 remains open because board and documentation maintenance
  continue throughout the project.
