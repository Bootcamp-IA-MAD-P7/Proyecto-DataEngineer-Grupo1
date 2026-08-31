# Task packet — HRP-53

**Status:** Draft
**Owner:** Johans
**Human reviewer:** Miguel
**Jira:** HRP-53
**Spec:** `docs/specs/HRP-53-postgres-docker.md`
**Planned branch:** `feature/HRP-53-postgres-docker`

## Expected outcome

A local, reproducible, healthy PostgreSQL service added to `infra/compose.dev.yml`,
following the same pattern already established by MongoDB in HRP-33, without
creating any table, schema or business data.

## Authorised context

- Briefing / document: Jira task HRP-53, child of HRP-39.
- Relevant local documentation: `infra/compose.dev.yml`, `infra/README.md`,
  `.env.example`, `docs/07-runbook.md`, `docs/adr/0004-configuration-and-secrets.md`,
  `docs/specs/HRP-62-application-dockerfile.md`,
  `docs/specs/HRP-64-environment-configuration.md`.
- Observed Kafka evidence (if applicable): not applicable; this task does not touch
  the Kafka/MongoDB contract.
- Related decisions or ADRs: ADR-0002, ADR-0004.

## Dependencies and limits

- Depends on: nothing formal in Jira. Independent of HRP-52, per the note already
  recorded in `docs/specs/HRP-52-tablas-relaciones.md`.
- Does not include: creating tables, keys or indexes (HRP-54), or the full
  application + MongoDB + PostgreSQL Compose stack (HRP-63), both blocked by or
  dependent on this task's outcome.
- Risk or unknown: none beyond a Compose variable-resolution detail, verified
  empirically and documented in the spec (`env_file` vs. `${VAR}` substitution).
- Constraint: do not read, clone or analyse the educational data generator.

## Request to the assistant

**Role:** Data architecture reviewer/designer (serving-engineer).
**Concrete question:** Does the Compose service provision a healthy, empty
PostgreSQL engine without creating a table, schema or business rule, and without
touching the existing `mongo` service?
**Expected output format:** a Compose service definition, environment-variable
catalogue changes, documentation updates, and real startup/healthcheck evidence.
**Evaluation criteria:** coherence with the HRP-33 MongoDB pattern, no invented
schema or business rule, Miguel's review.

## Human review of the result

- [ ] Facts and assumptions are separated.
- [ ] Cited paths and references exist.
- [ ] No field, topic or Kafka behaviour is invented.
- [ ] The proposal respects scope and security constraints.
- [ ] The result has been applied or discarded, with a stated reason.

## AI usage log

- Tool / role: Claude Code, data architecture reviewer/designer role
  (serving-engineer).
- Date: 2026-08-31.
- Summary of output: added a `postgres` service to `infra/compose.dev.yml`
  following the existing `mongo` pattern, extended `.env.example` with
  `POSTGRES_HOST`/`POSTGRES_PORT`, updated `infra/README.md`, `docs/07-runbook.md`
  and the root `README.md`, and wrote `docs/specs/HRP-53-postgres-docker.md`. No
  table, schema or business rule was created.
- Human decision: pending.
- Reviewer: Miguel (review pending).
