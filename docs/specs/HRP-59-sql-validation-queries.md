# HRP-59 — SQL validation queries for curated data

**Status:** Draft; not yet implemented
**Owner:** Johans Salas
**Human reviewer:** Miguel or Gaby
**Jira:** HRP-59 — Crear consultas SQL para validar la información final
**Dependencies:** HRP-54 (PostgreSQL schema, merged); HRP-55 (`person_mapper`,
merged); HRP-56/57/58 (`PersonRepository`, merged); HRP-60 (grouped-data
persistence verification, merged via [PR #54](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/54));
ADR-0006 (`Accepted in principle`)
**Related ADR:** [`docs/adr/0006-person-correlation-key.md`](../adr/0006-person-correlation-key.md)
**Planned branch:** `feature/HRP-59-sql-validation-queries`

## Objective

Provide a documented, reviewable library of read-only SQL validation queries that
repeatably checks the integrity of curated PostgreSQL data — built on the
persistence evidence already accepted in HRP-60 — without introducing a query API
and without asserting a business identity that ADR-0006 has not approved.

## Context and scope

### Verified preconditions (checked against `develop` before drafting this spec)

- HRP-60's merge commit (PR #54) is on `develop`, and re-running
  `tests/integration/test_grouped_data_persistence.py` against the live
  HRP-53 container confirms its four scenarios still pass (`4 passed`).
- `docs/adr/0006-person-correlation-key.md` status is exactly
  `Accepted in principle`; its "Responsibility boundaries" section still excludes
  real-world identity, database uniqueness and business-identity resolution.
- HRP-59 has no open Jira blocker of its own (checked directly on the Jira issue:
  its "is blocked by" HRP-60 now shows `Finalizada`). Its "blocks" link to HRP-56
  is historical and already satisfied (merged).
- No `docs/specs/HRP-59-*.md`, branch, PR, `.sql` file or validation-query module
  existed before this task — this is a greenfield design, not an extension.

### Includes

- A new, read-only module,
  [`src/hr_pro_platform/storage/validation_queries.py`](../../src/hr_pro_platform/storage/validation_queries.py),
  exposing one function per validation check, each built with `psycopg`'s
  `sql.SQL`/`sql.Identifier` (never string interpolation), consistent with
  `person_repository.py` and `postgres.py`.
- Checks covering: presence of the foreign-key constraints the schema declares;
  dependent-table rows with no matching `employees` row (orphans); employees
  missing one or more dependent domains (incomplete components, mirroring
  HRP-50's `incomplete` status once persisted); exact-duplicate dependent rows
  under the same `employee_id`; duplicate non-null `raw_event_ref` values in
  `processing_audit`; and aggregate row counts per curated table.
- Integration test evidence for every check, run against the live HRP-53
  container with minimal synthetic data inserted by the test itself (not
  assumed to pre-exist in the container).
- An explicit statement, next to every check, of what a "clean" result does and
  does not prove.

### Excludes (out of scope, do not touch)

- Any application or API code that runs these queries automatically or exposes
  them over HTTP. `src/hr_pro_platform/api/` stays empty; this task does not
  fill it.
- Re-verifying grouped-data persistence end-to-end with new integration tests —
  HRP-60 already did that. HRP-59 builds the reusable validation-query library
  itself; it does not repeat HRP-60's pipeline-level verification.
- Any change to the PostgreSQL schema (HRP-54), Docker (HRP-53), or the
  insert/update/deduplication logic already implemented in `person_repository.py`
  (HRP-55/56/57/58).
- Resolving or advancing the person correlation key (ADR-0006 stays
  `Accepted in principle`, not final).
- Any change to `ingestion/`, `transformation/`, Kafka or MongoDB.

## Design

### Module placement

`validation_queries.py` lives under `storage/`, alongside `person_repository.py`
and `postgres.py`, rather than under the still-empty `api/` package: these are
direct-to-database read functions with no HTTP concern, matching `storage`'s role
as "repository adapters" per `docs/backend-standards.md`. That same document
states `storage` "must not contain business decisions" — read-only technical
integrity checks (referential integrity, duplicate detection, completeness
counts) are not business decisions, the same reasoning already applied to
`processing_audit`'s technical idempotency tracking in HRP-58. The module defines
its own explicit column tuples for exact-duplicate detection rather than
importing `person_repository.py`'s private `_DEPENDENT_TABLE_COLUMNS`, to avoid
coupling a read-only validation module to a private implementation detail of the
write path; the two are expected to be kept in sync by the schema they both
describe (HRP-54), not by direct code sharing.

### Checks

| Function | What it checks | What a clean result proves | What it does NOT prove |
|---|---|---|---|
| `check_foreign_key_constraints_present` | Each dependent table (`locations`, `professional_profiles`, `bank_accounts`, `network_data`) has a `FOREIGN KEY` constraint on `employee_id` referencing `employees` | The schema still enforces referential integrity at the database level | Data already violating it before the constraint existed (impossible under normal operation, but not ruled out by this check alone) |
| `find_orphaned_dependent_rows` | Rows in a dependent table whose `employee_id` has no matching row in `employees` | No dependent row is currently orphaned | Nothing about future inserts; relies on the FK constraint from the previous check still being present |
| `find_incomplete_employees` | Employees with zero rows in one or more dependent tables | Which employees persisted so far are missing which domain(s) | Whether that is expected (a genuinely incomplete HRP-50 component) or a defect — this check is informational, not a pass/fail signal by itself |
| `find_exact_duplicate_dependent_rows` | Two or more rows in the same dependent table, same `employee_id`, identical on every non-id column | HRP-57's NULL-safe full-column exact-match enrichment check has not been bypassed for the inspected data | Nothing about a `source_reference` that was never reprocessed |
| `find_duplicate_processing_audit_references` | Non-null `raw_event_ref` values appearing in more than one `processing_audit` row | HRP-58's unique index has not been dropped or bypassed | Nothing about `raw_event_ref` values recorded before the index existed |
| `count_rows_per_table` | Aggregate row count for each curated table | A quick manual sanity snapshot | Nothing about correctness of the data itself |

No check in this module compares, aggregates or infers a real-world person
identity. Every check that touches correlated data (e.g. incomplete-employee
detection) is scoped to what is already persisted per an approved ADR-0006 edge,
never to an identity claim ADR-0006 does not make.

## What stays provisional / unknown / pending

- No check may claim a persisted row proves real-world identity; ADR-0006
  remains `Accepted in principle`, not final.
- Checks are scoped to the five curated tables and `processing_audit` that exist
  today (HRP-54/58); a future table or domain requires its own reviewed addition
  to this module, not a silent extension.
- `find_incomplete_employees` is explicitly informational, not a defect signal —
  an incomplete component is an expected, documented HRP-50 outcome, not
  necessarily an error.

## Acceptance criteria

- [ ] `validation_queries.py` exists under `storage/`, is read-only, and uses
      `psycopg`'s `sql.SQL`/`sql.Identifier` exclusively (no string interpolation).
- [ ] Covers, at minimum: FK-constraint presence, orphaned dependent rows,
      incomplete employees, exact-duplicate dependent rows, duplicate
      `processing_audit.raw_event_ref`, and per-table row counts.
- [ ] Every check has integration-test evidence against real PostgreSQL with
      synthetic data inserted by the test itself.
- [ ] No check asserts real-world identity or a correlation key ADR-0006 has not
      approved.
- [ ] No change to schema, Docker, insert/update/deduplication logic, or any
      `api/` code.
- [ ] This specification is complete per `docs/specs/template.md`.

## Accessibility and sustainability applicability

- Accessibility: not applicable — read-only backend queries with no user-facing
  flow.
- Sustainability: applicable through reuse of the existing PostgreSQL dev
  container and repository code; no new service, dependency or persistent store
  is introduced. No carbon, energy or deployment claim is made.
- Deferred claims: none beyond the above.

## Test strategy

| Nivel | Caso | Evidencia esperada |
|---|---|---|
| Integración | Cada tabla dependiente declara su FK a `employees` | Contenedor HRP-53 real; consulta a `information_schema`/`pg_constraint` |
| Integración | Ninguna fila dependiente queda huérfana tras un insert normal | Contenedor real; cero filas huérfanas con datos sintéticos insertados |
| Integración | Un empleado con dominios ausentes se detecta correctamente | Contenedor real; empleado sintético con solo `employees`+`bank_accounts` |
| Integración | Una fila duplicada exacta bajo el mismo `employee_id` se detecta | Contenedor real; fila insertada dos veces directamente (bypaseando `person_repository`) para simular el caso |
| Integración | Un `raw_event_ref` duplicado en `processing_audit` se detecta | Contenedor real; segunda fila insertada directamente (bypaseando el índice único, o verificando que el índice lo impide) |
| Integración | Conteos por tabla reflejan los datos sintéticos insertados | Contenedor real; conteo exacto esperado |

## Evidencia de cierre

- Rama: `feature/HRP-59-sql-validation-queries`; PR: pending
- Commit: pending (se añade tras el commit final de implementación)
- Comandos ejecutados y resultado:
  - `pre-commit run --all-files` → passed
  - `ruff check .` / `ruff format --check .` → passed
  - `mypy src` → `Success: no issues found in 27 source files`
  - `pytest` (suite completa contra PostgreSQL real,
    `docker compose -f infra/compose.dev.yml up -d postgres`) →
    `204 passed, 2 skipped in 22.37s` (skips son solo MongoDB, no relacionados)
  - Prueba de mutación: se cambió temporalmente `count == 0` a `count == 1` en
    `find_incomplete_employees` y se confirmó que
    `test_incomplete_employee_reports_its_missing_domains` falla — evidencia de
    que la aserción es sensible al comportamiento real, no vacía. Restaurado
    tras la verificación (backup manual, sin `git checkout` sobre trabajo no
    commiteado).
- Comentario Jira con el resultado: pending (se redacta tras aprobación de PR)
