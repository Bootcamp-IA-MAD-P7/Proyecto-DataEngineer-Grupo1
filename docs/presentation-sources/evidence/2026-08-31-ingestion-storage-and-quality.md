# Evidence — 2026-08-31 ingestion, storage and quality baseline

## Purpose

This evidence source records the current demonstrable state after the latest ingestion
and documentation merges. It is intended for NotebookLM and the technical
presentation. It does not contain Kafka payload values, secrets, offsets or generator
source information.

## Verified evidence

| Evidence | Result |
|---|---|
| Latest `develop` commit reviewed | `0942230` |
| Latest `quality` workflow on `develop` | Success |
| Tests | 17 passed |
| Coverage | 80.10 % |
| Coverage threshold | 75 % |
| Specs validated by CI | 16 |
| Type checking | `mypy src` passed |
| Lint and format | Ruff passed |
| Compose validation | `docker compose -f infra/compose.dev.yml config --quiet` passed |

## Functional progress

The platform has moved beyond a purely documented foundation. It now includes:

- configurable Kafka consumer code;
- continuous polling with technical-only logs;
- MongoDB client connection with `ping`;
- MongoDB indexes for technical lookup and duplicate protection;
- initial batch insertion of valid fragments;
- tests covering consumer, MongoDB client, duplicate handling and retry boundaries.

## Limits

This is not yet the final end-to-end demo. The current implementation still needs a
reviewed boundary between raw Kafka metadata, raw payload storage and derived fragment
classification before the ETL worker relies on MongoDB as its source.

The project still lacks:

- complete person correlation;
- approved classification rules for all variants;
- business validation and cleaning rules;
- PostgreSQL service, migrations and writes;
- API, frontend, Redis and Prometheus.

## Presentation angle

The differentiator is traceability under pressure: the team encountered real CI and
review friction, fixed it through small PRs, and now has a cleaner route to finish the
essential pipeline without pretending that planned capabilities are already complete.
