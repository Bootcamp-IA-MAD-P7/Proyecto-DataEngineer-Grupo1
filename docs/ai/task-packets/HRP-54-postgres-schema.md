# Task packet — HRP-54

**Status:** Draft
**Owner:** Johans
**Human reviewer:** Miguel
**Jira:** HRP-54
**Spec:** `docs/specs/HRP-54-postgres-schema.md`
**Planned branch:** `feature/HRP-54-postgres-schema`

## Expected outcome

A real, idempotent PostgreSQL schema (tables, primary keys, candidate foreign
keys and indexes) created against the HRP-53 engine, exactly matching the design
already approved in `docs/specs/HRP-52-tablas-relaciones.md`, with no unauthorised
business rule and no assumed cardinality.

## Authorised context

- Briefing / document: Jira task HRP-54, child of HRP-39.
- Relevant local documentation: `docs/specs/HRP-52-tablas-relaciones.md`,
  `docs/specs/HRP-25-modelo-datos.md`, `infra/compose.dev.yml`,
  `docs/backend-standards.md`, `docs/adr/0006-person-correlation-key.md`.
- Observed Kafka evidence (if applicable): not applicable; this task does not
  touch the Kafka/MongoDB contract.
- Related decisions or ADRs: ADR-0002, ADR-0006 (remains `Proposed`).

## Dependencies and limits

- Depends on: HRP-52 (design, merged) and HRP-53 (Docker service, merged).
- Does not include: ETL/correlation logic (HRP-55, blocked on Gaby's work), API
  code, a migration framework, or the exhaustive SQL persistence test suite
  (HRP-70).
- Risk or unknown: column-type defaults for `sex`, `salary`, `ip_v4` and
  `raw_event_ref`, documented explicitly in the spec as reversible defaults.
- Constraint: do not read, clone or analyse the educational data generator.

## Request to the assistant

**Role:** Data architecture reviewer/designer (serving-engineer).
**Concrete question:** Does the schema-creation code faithfully implement
HRP-52's candidate design, with no unique business constraint and no assumed
cardinality, and is it idempotent against a real running PostgreSQL instance?
**Expected output format:** a storage module, unit and integration tests, and
real schema-verification evidence.
**Evaluation criteria:** coherence with HRP-52/HRP-25, no invented schema or
business rule, Miguel's review.

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
- Summary of output: implemented `src/hr_pro_platform/storage/postgres.py`
  (idempotent `CREATE TABLE IF NOT EXISTS`/`CREATE INDEX IF NOT EXISTS` schema
  creation), `storage/config.py`, unit tests (mocked) and a real integration test
  against the HRP-53 container, and wrote `docs/specs/HRP-54-postgres-schema.md`
  documenting the schema-creation mechanism and four reversible column-type
  defaults. No ETL, correlation or API code was added.
- Human decision: pending.
- Reviewer: Miguel (review pending).
