# HRP-86 — Statistics endpoint

**Status:** Draft; implementation authorised — the metrics-list open decision
below was confirmed by Johans Salas (task owner) on 2026-09-04, adopting the
proposed minimal default as-is. Revised on 2026-09-04 after Gabriela Granja's
review of PR #69 (`CHANGES_REQUESTED`): the aggregation model changed from
reusing `find_incomplete_employees()` (per-employee, materialized in Python)
to a new, dedicated PostgreSQL aggregate query
(`count_employees_missing_each_domain()`), and the response contract changed
from `dict[str, int]` to explicit Pydantic models. See "Design" and
"Decisions confirmed after review" below.
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

- New function `count_employees_missing_each_domain()` in
  `storage/validation_queries.py` (HRP-59's module, not modifying any
  existing function there): a single query,
  `SELECT count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM {table} d WHERE
  d.employee_id = e.id)) AS {table}, ... FROM employees e`, one `FILTER`
  clause per dependent table. This returns exactly one row of four integers
  — the database itself does the aggregation; no per-employee row is ever
  fetched or reduced in Python. It intentionally does **not** reuse
  `find_incomplete_employees()`, which answers a different question ("which
  employees are missing which domains", one row per employee) at a cost
  proportional to the employee count, unsuitable for an endpoint that only
  needs four constant-size counters.
- New module `src/hr_pro_platform/api/statistics.py`: two explicit response
  models, `RowsPerTable` (six named `int` fields, one per curated table) and
  `EmployeesMissingDomain` (four named `int` fields, one per dependent
  table), composed into `StatisticsResult`. Every field name is part of the
  API contract and appears in the generated OpenAPI schema; no field can be
  silently added, removed or renamed without a visible model change, and no
  per-record field (an `employee_id`, an `iban`/`salary`, etc.) can appear
  without one either — a structural guarantee, not just a runtime check.
  `compute_statistics(cursor)` calls `count_rows_per_table(cursor)` and
  `count_employees_missing_each_domain(cursor)` and maps each result dict
  directly onto its model (`Model(**result)`); no iteration over employees
  happens anywhere in this module.
- `GET /statistics` in `main.py` opens a cursor via the existing
  `get_connection` dependency and returns `compute_statistics(cursor)`
  directly — same shape as `/health`, no filters to validate.
- Error handling: unchanged, reuses `main.py`'s existing `psycopg.Error`
  handler.

### Decisions confirmed after review (addressing Gabriela Granja's PR #69 review)

1. **Aggregation moved into PostgreSQL — CONFIRMED.** Per the "Design"
   section above: `count_employees_missing_each_domain()` computes the four
   counts as PostgreSQL aggregates in one query, never materializing a
   per-employee row. `find_incomplete_employees()` remains untouched and
   unused by this endpoint.
2. **Explicit response contract — CONFIRMED.** `RowsPerTable` and
   `EmployeesMissingDomain` replace the original `dict[str, int]` fields.
3. **No-individual-data guarantee — CONFIRMED as structural.** Tested
   directly against the Pydantic models' field sets and field types
   (`tests/unit/test_api_statistics.py::test_response_models_only_expose_allowed_aggregate_fields`),
   not only against one response instance's keys.
4. **Integration-test runtime (151.44s originally reported) — investigated.**
   Every real-PostgreSQL integration test run manually in this development
   environment during HRP-84/85/86 (a Windows host with Docker Desktop) has
   taken between roughly 140 and 300 seconds, regardless of query
   complexity — including `GET /health`-adjacent round-trips with a single
   trivial query. This is consistent with connection/schema-creation
   latency specific to this local Docker setup, not with the cost of the
   query under test. As direct evidence for this specific case: the runtime
   of `test_statistics_reflects_inserted_employees_and_missing_domains`
   after replacing the O(employees) Python-side reduction with a single
   O(1) aggregate query is recorded in "Closing evidence" below — if it did
   not meaningfully drop, that confirms the bottleneck is environmental, not
   the query.
5. **Spec state — CONFIRMED updated**, this revision.

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
- [x] `employees_missing_domain` matches `count_employees_missing_each_domain()`'s
      output exactly, computed entirely as PostgreSQL aggregates — no
      per-employee row is fetched to answer this endpoint.
- [x] The response contract uses explicit Pydantic models (`RowsPerTable`,
      `EmployeesMissingDomain`), not an unrestricted `dict[str, int]`.
- [x] No individual `employee_id`, `iban`, `salary`, or any other per-record
      field can appear in the response — guaranteed structurally by the
      response models' field sets, verified by a test that inspects the
      models directly, not only one response instance.
- [x] Database failures are handled by the existing `psycopg.Error` handler;
      no new logging path is introduced.
- [x] No HRP-89/90/91 logic, no schema/Docker/Kafka/Mongo/Redis change, no
      change to `people.py`'s existing routes or `validation_queries.py`'s
      existing functions (`count_employees_missing_each_domain()` is a new
      addition, not a modification).
- [x] `docs/specs/HRP-86-statistics-endpoint.md` complete per
      `docs/specs/template.md`.

## Accessibility and sustainability applicability

- Accessibility: not applicable — this is a JSON API response with no
  rendered interface; the Streamlit frontend (HRP-91) that will consume it is
  a separate, later task that will assess accessibility for its own UI.
- Sustainability: applicable — a single bounded aggregate snapshot (six
  `COUNT(*)` queries plus one `FILTER`-based aggregate query over
  `employees`, all constant-result-size regardless of table size), no
  pagination, no per-employee data transferred, no new persistent
  connection or background process beyond the existing per-request pattern.
- Deferred claims: no performance, throughput or production-readiness claim
  is made; no claim about query cost at a scale larger than currently tested.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Unit | `count_employees_missing_each_domain()` maps one aggregate row, in table order, using `NOT EXISTS`/`FILTER`, never `JOIN`, never a per-employee `fetchall` | `tests/unit/test_validation_queries.py`, mocked cursor, asserts rendered SQL and call counts |
| Unit | `compute_statistics()` issues only 7 aggregate `fetchone` calls, zero `fetchall` calls | Direct call, fully mocked cursor, call-count assertions |
| Unit | `GET /statistics` returns the computed result, no query params needed | `TestClient`, dependency override with fixture cursor |
| Unit | Database failure | Reuses the existing handler; `503`, no message leak |
| Unit | Response models expose only the allowed aggregate integer fields — structural guarantee | Assertions on `RowsPerTable`/`EmployeesMissingDomain`'s own `model_fields` and field types, not just one response instance |
| Integration | `count_employees_missing_each_domain()` real round-trip with **delta assertions**, not absolute counts | Real PostgreSQL container, `tests/integration/test_validation_queries.py`, baseline captured before insert, exact delta asserted, restored-to-baseline asserted after cleanup |
| Integration | `GET /statistics` real round-trip with **delta assertions** | Real PostgreSQL container: capture a baseline via `GET /statistics`, insert synthetic employees with distinguishable missing/present domains, assert the *difference* from baseline matches the exact expected delta per table and per domain, then clean up and assert the response returns exactly to baseline |

## Closing evidence

### First implementation (PR #69, commit `c0b536e`)

- Branch: `feature/HRP-86-statistics-endpoint`, created from `origin/develop`
  at `e0306a1`. PR: [#69](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/69).
- Reviewed by Gabriela Granja on 2026-09-04 (`CHANGES_REQUESTED`): required
  moving the `employees_missing_domain` aggregation into PostgreSQL instead
  of reusing `find_incomplete_employees()`, making the response contract
  explicit instead of `dict[str, int]`, strengthening the no-individual-data
  guarantee structurally, investigating the ~151s integration-test runtime,
  and updating this spec's stale closing evidence. See "Decisions confirmed
  after review" above for how each point was addressed.
- Original validation (superseded by the revision below, kept for
  traceability): `pytest tests/unit` → `237 passed` in 7.19s; real-PostgreSQL
  integration → `1 passed in 151.44s`.

### Revision addressing the review (commit pending)

- Rebased onto `origin/develop` at `a0929b6` (post PR #67, HRP-75/Redis
  retrieval) — no conflicts, no file overlap.
- Commands executed and result:
  - `python -m ruff check .` → all checks passed.
  - `python -m ruff format .` → 1 file reformatted (`storage/validation_queries.py`,
    line-length only), no logic change.
  - `python -m mypy src` → `Success: no issues found in 34 source files`.
  - `python -m pytest tests/unit --no-cov` → `250 passed` in 6.19s (13 more
    than before: the new `count_employees_missing_each_domain()` unit test,
    the revised `compute_statistics()`/route tests, and the structural
    model-field test).
  - `python -m pytest tests/integration/test_api_statistics.py
    tests/integration/test_validation_queries.py::test_count_employees_missing_each_domain_reflects_a_delta
    -v --no-cov` against a real PostgreSQL container (already running) →
    both **passed** (`2 passed in 281.64s`, ≈140s each). This is the same
    order of magnitude as the original single test's 151.44s — switching
    from an O(employees) Python-side reduction to a single O(1) PostgreSQL
    aggregate query did not meaningfully change the per-test runtime,
    confirming the earlier concern's runtime is environmental
    (connection/schema-creation latency specific to this local Windows +
    Docker Desktop setup, observed consistently across every HRP-84/85/86
    real-PostgreSQL integration test run manually this session, regardless
    of query complexity), not the cost of the query itself. No leftover
    synthetic rows confirmed via `SELECT ... WHERE passport LIKE 'HRP86%' OR
    passport LIKE 'HRP59-P-MISSING%'` → 0 rows.
  - `python scripts/validate_specs.py` → passed, 50 specs validated.
  - `python -m pre_commit run --all-files` → all hooks passed.
- Human reviewer approval: pending re-review from Gabriela Granja (and the
  still-outstanding requests to Miguel/Anahí).
- Jira closing comment: pending; closure is not authorised by this draft.
