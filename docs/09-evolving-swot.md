# Evolving SWOT and delivery health

## Purpose

This is a living project-control artifact, not marketing copy. It is updated after
every functional milestone and before each presentation rehearsal. Every claim must
point to merged code, a reviewed document, a test result or a Jira state.

## Current snapshot — 2026-08-28

| Strengths | Weaknesses |
|---|---|
| Evidence-first Kafka contract prevents invented semantics. | The essential Kafka-to-Mongo-to-ETL-to-PostgreSQL path is incomplete. |
| SDD, ADRs, CODEOWNERS, CI and human review are operational. | The executable codebase is still small and currently has only 7 tests. |
| Kafka connectivity, safe observation and continuous consumption are validated. | MongoDB raw persistence, correlation and SQL persistence are not yet demonstrable. |
| Team ownership and presentation evidence have canonical locations. | Contribution and integration load is currently concentrated on Miguel. |

| Opportunities | Threats |
|---|---|
| Deliver a reliable raw envelope and idempotency as the next vertical slice. | Scope expansion into Redis, API, Airflow or dashboards before Essential is stable. |
| Add structured PII-safe logging, integration tests and healthchecks incrementally. | Long-lived multi-task branches can overwrite reviewed implementations. |
| Turn CI, Jira evidence and the live pipeline into a differentiated technical demo. | Weak correlation evidence could merge records from different people. |
| Ratchet coverage and performance evidence as the codebase grows. | Documentation can drift and describe target capabilities as current behaviour. |

## Delivery health

| Dimension | Score | Evidence | Target for next review |
|---|---:|---|---|
| Functional completeness | 2/5 | Kafka validated; raw and curated path incomplete | MongoDB raw persistence proven |
| Data correctness | 3/5 | Observed contract reviewed; correlation remains unknown | HRP-43 decision with tests |
| Quality automation | 4/5 | CI, Ruff, mypy, pytest, spec validation and reviews | Coverage + Compose checks enforced |
| Operability | 2/5 | Consumer and Mongo service run locally | Failure/acknowledgement integration test |
| Documentation and traceability | 4/5 | Specs, ADRs, dailies, PR and Jira evidence | Eliminate stale completion markers |
| Team flow | 2/5 | Four owners assigned; review is active | Each area contributes a reviewed PR |

Scores measure current evidence, not ambition: 1 is absent, 3 is usable but incomplete,
and 5 is demonstrated, automated and repeatable.

## Review protocol

1. Update the snapshot after each level of the briefing or material architecture change.
2. Replace resolved weaknesses and threats instead of deleting history.
3. Add a row to the history with the evidence that changed a score.
4. Use the presentation adaptation in `docs/presentation-sources/02-evolving-swot.md`.

## Evolution history

| Date | Milestone | Change in assessment | Evidence |
|---|---|---|---|
| 2026-08-28 | Kafka foundation and benchmark | Baseline created; quality is ahead of functional completeness | PRs #10, #12 and #14; 7 tests; Kafka runtime validation |
