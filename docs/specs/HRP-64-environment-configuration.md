# HRP-64 — Configure environment variables

**Status:** Draft; documentary implementation authorised
**Owner:** Miguel
**Jira:** HRP-64
**Dependencies:** ADR-0004 accepted; no runtime service implementation is required
**Related ADR:** `docs/adr/0004-configuration-and-secrets.md`
**Planned branch:** `feature/HRP-64-environment-configuration`

## Objective

Provide one safe, reproducible environment-configuration contract for local
development. Contributors must be able to discover which variables exist, where
their values belong, and which configuration is already consumed at runtime without
committing secrets or inventing service behaviour.

## Scope and boundaries

### Includes

- Document the existing variables in `.env.example` in the README and runbook.
- State the precedence rule: process environment values take priority over the local
  `.env` file.
- Identify the current consumer of each variable or mark it as reserved for a future
  task.
- Preserve `.env.example` as the versioned template and `.env` as a local-only file.

### Excludes

- New application configuration classes, secret-management tooling, Docker services,
  database connections, ETL logic, or new dependencies.
- Hard-coded broker addresses, credentials, payload details, or environment-specific
  values beyond the non-sensitive examples already present in `.env.example`.
- Changes to the educational Kafka generator or its source code.

### Assumptions and risks

- `load_kafka_settings()` currently consumes only the three `KAFKA_*` variables.
- MongoDB, PostgreSQL, Redis, and log-level variables are documented for planned
  components; documenting them does not claim that their runtime consumers exist.
- The local `.env` file may contain secrets and must never be read into evidence,
  commits, PR text, or Jira comments.

## Design

`.env.example` remains the canonical versioned variable-name template. The README is
the concise onboarding reference and `docs/07-runbook.md` is the operational
reference. Both must distinguish active Kafka configuration from reserved variables
for future services.

The existing Kafka loader uses `python-dotenv` with `override=False`; therefore a
value explicitly supplied by the process environment takes precedence over `.env`.
No source-code change is necessary for this task.

## Acceptance criteria

- [ ] Every variable already present in `.env.example` is described in the README.
- [ ] The runbook explains safe creation and handling of a local `.env` file.
- [ ] Active Kafka variables and reserved future-service variables are clearly
      distinguished.
- [ ] Documentation states that `.env` values are never committed or copied into PRs,
      Jira, logs, chats, or presentation material.
- [ ] Documentation states that process environment values take precedence over
      `.env` for the current Kafka consumer.
- [ ] No new environment variable, secret, Docker service, runtime dependency, or
      payload information is introduced.

## Validation strategy

| Level | Case | Expected evidence |
|---|---|---|
| Documentary | All `.env.example` names appear in the configuration catalogue | Manual cross-check |
| Security | No `.env` value or credential appears in the diff | Manual diff review |
| Specification | HRP-64 spec follows the repository template | `validate task specifications` hook |
| Quality | Repository checks remain clean | `pre-commit`, Ruff, mypy, pytest where executable |

## Closing evidence

- Branch / PR: pending.
- Commit: pending.
- Commands and results: pending.
- Jira comment: pending; the task remains In Progress until a human reviews the PR.
