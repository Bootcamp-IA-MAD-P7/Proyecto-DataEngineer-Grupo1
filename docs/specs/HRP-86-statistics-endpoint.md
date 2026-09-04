# HRP-86 — Statistics endpoint

**Status:** Draft; implementation authorised — the metrics-list open decision
below was confirmed by Johans Salas (task owner) on 2026-09-04, adopting the
proposed minimal default as-is.
**Owner:** Johans Salas
**Human reviewer:** Miguel or Gaby
**Jira:** HRP-86 — Crear endpoint de estadísticas
**Dependencies:** HRP-83 (API skeleton, merged, Jira: Finalizada); HRP-59
(`storage/validation_queries.py`, merged) — no formal "depends on" link to
HRP-84/HRP-85 in Jira, but both of their specs explicitly reserve "statistics
endpoint" as HRP-86's scope.
**Related ADR:** [`docs/adr/0006-person-correlation-key.md`](../adr/0006-person-correlation-key.md)
**Planned branch:** `feature/HRP-86-statistics-endpoint`

## Objective

Add a third read-only endpoint on top of HRP-83's API skeleton, exposing
aggregate statistics over curated PostgreSQL data — row counts per table and
how many employees are missing each dependent domain — without exposing any
individual employee, location, professional, bank or network record.

## Context and scope

### Verified preconditions (checked against `origin/develop` before drafting this spec)

- HRP-83, HRP-84 and HRP-85 are merged into `develop`. `src/hr_pro_platform/api/main.py`
  exposes `create_app()` with `GET /health`, `GET /people/search` and
  `GET /people/search/by-location-profession`, all depending on
  `Annotated[psycopg.Connection[...], Depends(get_connection)]` from `api/db.py`.
- `src/hr_pro_platform/storage/validation_queries.py` (HRP-59, merged) already
  provides `count_rows_per_table()` (per-table `COUNT(*)`, no `JOIN`) and
  `find_incomplete_employees()` (per-employee missing-domain detection via a
  correlated subquery per dependent table, not a `JOIN`) — both already avoid
  the row-multiplication risk of joining `employees` to a 1:N dependent table.
- No `docs/specs/HRP-86-*.md`, branch or PR existed before this task.
- HRP-86 has one formal Jira blocker, HRP-83, already `Finalizada`. HRP-86
  blocks HRP-91 (Streamlit metrics view), which must not start before this is
  approved.
- ADR-0006 is `Accepted in principle`, not final — unchanged since HRP-84/85.

### Includes

- One new route, `GET /statistics`, added inside `create_app()` alongside the
  existing routes. No query parameters, no pagination — a single aggregate
  snapshot.
- Two aggregate metrics, computed by directly reusing HRP-59's existing
  functions rather than writing new SQL:
  - `rows_per_table`: a row count for every curated table (`employees`,
    `locations`, `professional_profiles`, `bank_accounts`, `network_data`,
    `processing_audit`), from `count_rows_per_table()`.
  - `employees_missing_domain`: for each dependent table, how many employees
    currently have zero rows there, aggregated from
    `find_incomplete_employees()`'s per-employee result into a per-domain
    count. No `employee_id` is ever included in the response — only the
    aggregate count.
- Reuse of `main.py`'s existing `psycopg.Error` handler for database failures.
- Unit tests (dependency override, no real database) and one integration test
  against a real PostgreSQL container using delta assertions (see "Test
  strategy").

### Excludes (out of scope, do not touch)

- HRP-89/HRP-90 (Streamlit frontend) — this task only adds the API route they
  will later call. HRP-91 (metrics view) is the specific consumer.
- Any schema change, any change to `person_repository.py`'s write path, any
  Docker/Kafka/MongoDB/Redis change.
- Any change to `storage/validation_queries.py`'s existing functions or to
  `api/people.py`'s existing routes.
- Any individual record: no `employee_id`, no `iban`/`salary` value, no
  `city`/`job`/`address` value. This endpoint returns counts only.
- Any authentication/authorization layer — none exists yet in any task so far.
- Resolving or asserting real-world person identity, or declaring a person
  "complete" — `employees_missing_domain` is informational, mirroring
  `find_incomplete_employees()`'s own documented caveat that a missing domain
  is an expected HRP-50 outcome, not necessarily a defect.

### Open decision this spec resolves (human call)

**Exact metrics list.** Neither HRP-86 nor HRP-91 define this in Jira (both
tickets have no description). Two aggregate metrics are proposed and
**confirmed as the minimal default** for this task: `rows_per_table` and
`employees_missing_domain`, both derived from already-reviewed,
already-tested `validation_queries.py` functions rather than new,
unevidenced business metrics. Including `bank_accounts` in `rows_per_table`
and `employees_missing_domain` is a deliberate, confirmed choice: only an
aggregate *count* is exposed, never an individual `iban`/`salary` value —
this is a different exposure than HRP-84/85's exclusion of the
`bank_accounts` table from a per-employee search response, and is treated
here as an explicitly confirmed, narrower decision, not a silent expansion of
scope. A future task may add further metrics with its own spec.

## Design

- New module `src/hr_pro_platform/api/statistics.py`: a `StatisticsResult`
  Pydantic model (`rows_per_table: dict[str, int]`,
  `employees_missing_domain: dict[str, int]`) and `compute_statistics(cursor)`,
  which calls `count_rows_per_table(cursor)` and `find_incomplete_employees(cursor)`
  and aggregates the latter's per-employee result into per-domain counts.
  No new SQL is written for the counts themselves — only the aggregation from
  per-employee to per-domain happens in this new module, in Python.
- `GET /statistics` in `main.py` opens a cursor via the existing
  `get_connection` dependency and returns `compute_statistics(cursor)`
  directly — same shape as `/health`, no filters to validate.
- Error handling: unchanged, reuses `main.py`'s existing `psycopg.Error`
  handler.

## What stays provisional / unknown / pending

- Whether further metrics (e.g. counts grouped by `city`/`job`) are added —
  deferred to a future task with its own spec once a concrete consumer need
  is evidenced (HRP-91 currently has no description to evidence one).
- Authentication/authorization on this or any API route — still a known,
  unaddressed gap.
- Any statistic implying a resolved, verified real-world identity — ADR-0006
  remains `Accepted in principle`, not final.

## Acceptance criteria

- [x] The metrics-list open decision is confirmed and recorded in this spec
      before implementation.
- [x] `GET /statistics` exists, reachable through the existing `create_app()`
      factory, no query parameters required.
- [x] `rows_per_table` matches `count_rows_per_table()`'s output exactly.
- [x] `employees_missing_domain` matches a per-domain aggregation of
      `find_incomplete_employees()`'s output exactly.
- [x] No individual `employee_id`, `iban`, `salary`, or any other per-record
      field ever appears in the response.
- [x] Database failures are handled by the existing `psycopg.Error` handler;
      no new logging path is introduced.
- [x] No HRP-89/90/91 logic, no schema/Docker/Kafka/Mongo/Redis change, no
      change to `people.py`'s existing routes or `validation_queries.py`'s
      existing functions.
- [x] `docs/specs/HRP-86-statistics-endpoint.md` complete per
      `docs/specs/template.md`.

## Accessibility and sustainability applicability

- Accessibility: not applicable — this is a JSON API response with no
  rendered interface; the Streamlit frontend (HRP-91) that will consume it is
  a separate, later task that will assess accessibility for its own UI.
- Sustainability: applicable — a single bounded aggregate snapshot (fixed
  number of `COUNT(*)` queries plus one correlated-subquery query over
  `employees`), no pagination, no new persistent connection or background
  process beyond the existing per-request pattern.
- Deferred claims: no performance, throughput or production-readiness claim
  is made; no claim about query cost at a scale larger than currently tested.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Unit | `compute_statistics()` aggregates a mocked cursor's results into the exact expected `StatisticsResult` | Direct call, fully mocked cursor, exact dict comparison |
| Unit | `GET /statistics` returns the computed result, no query params needed | `TestClient`, dependency override with fixture cursor |
| Unit | Database failure | Reuses the existing handler; `503`, no message leak |
| Unit | No individual record field (`iban`, `salary`, `employee_id`, etc.) ever appears in the response | Assertion on the response JSON's key set |
| Integration | Real round-trip with **delta assertions**, not absolute counts (the database may already hold unrelated rows) | Real PostgreSQL container: capture a baseline via `GET /statistics`, insert synthetic employees with distinguishable missing/present domains, assert the *difference* from baseline matches the exact expected delta per table and per domain, then clean up and assert the response returns exactly to baseline |

## Closing evidence

- Branch: `feature/HRP-86-statistics-endpoint`, created from `origin/develop`
  at `e0306a1`. PR: pending.
- Commit: pending (not committed yet at spec-writing time).
- Commands executed and result:
  - `python -m ruff check .` → all checks passed.
  - `python -m ruff format .` → no changes needed.
  - `python -m mypy src` → `Success: no issues found in 34 source files`.
  - `python -m pytest tests/unit --no-cov` → `237 passed` in 7.19s.
  - `python -m pytest tests/integration/test_api_statistics.py -v --no-cov`
    against a real PostgreSQL container (`docker compose -f
    infra/compose.dev.yml up -d postgres`, already running) →
    **passed** (`1 passed in 151.44s`). Confirms the real round-trip: exact
    delta in `rows_per_table` and `employees_missing_domain` after inserting
    two synthetic employees with distinguishable missing/present domains,
    and that the response returns exactly to baseline after cleanup. No
    leftover synthetic rows confirmed via `SELECT ... WHERE passport LIKE
    'HRP86%'` → 0 rows.
  - `python scripts/validate_specs.py` → passed, 49 specs validated.
  - `python -m pre_commit run --all-files` → all hooks passed.
- Human reviewer approval: pending — not requested yet.
- PR not opened; Jira closing comment: pending; closure is not authorised by
  this draft.
