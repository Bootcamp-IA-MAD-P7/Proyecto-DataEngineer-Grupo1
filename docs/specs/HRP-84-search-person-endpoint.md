# HRP-84 — Search person endpoint

**Status:** Draft; not yet implemented
**Owner:** Johans Salas
**Human reviewer:** Miguel or Gaby
**Jira:** HRP-84 — Crear endpoint para buscar una persona
**Dependencies:** HRP-83 (API skeleton, merged); HRP-54 (PostgreSQL schema, merged)
**Related ADR:** [`docs/adr/0006-person-correlation-key.md`](../adr/0006-person-correlation-key.md)
**Planned branch:** `feature/HRP-84-search-person-endpoint`

## Objective

Add the first business endpoint on top of HRP-83's API skeleton: a read-only search
over the curated `employees` table (and its directly-owned, non-financial dependent
data) by already-persisted technical fields, returning the matching curated records —
never a claim of resolved real-world identity.

## Context and scope

### Verified preconditions (checked against `develop` before drafting this spec)

- HRP-83's merge commit is on `develop`; `src/hr_pro_platform/api/main.py` still
  exposes only `create_app()`, the shared `psycopg.Error` handler and `GET /health`;
  `api/db.py`'s `get_connection` dependency is unchanged.
- No `docs/specs/HRP-84-*.md`, branch or PR existed before this task.
- HRP-84 has no open Jira blocker (HRP-83 shows `Finalizada`); it blocks HRP-90
  (Streamlit search UI), which must not start before this is approved.

### Includes

- One new route, `GET /people/search`, added inside `create_app()` alongside
  `/health` (same file, same factory — no new router module needed at this size).
- Query-parameter filters over `employees` columns only: `passport` (exact),
  `first_name` (exact), `last_name` (exact), `id` (exact, the internal integer
  primary key). At least one filter is required; a request with none is rejected
  with `400`, not silently interpreted as "return everything."
- A bounded response: each match's `employees` columns (excluding nothing sensitive
  new — `sex`, `telephone_number`, `email`, `passport` are already the curated
  columns HRP-54 approved) plus its related `locations` and `professional_profiles`
  rows (both are already non-financial, already-curated data). Pagination via
  `limit` (default 20, max 100) and `offset` (default 0), both validated.
- Reuse of `api/main.py`'s existing `psycopg.Error` handler for database failures —
  no new error-logging code path. A separate, explicit `400` response for invalid
  query parameters (empty filter set, non-positive `limit`, negative `offset`).
- Unit tests (dependency override, no real database) for: a match found, no match
  found, missing-filter rejection, and a database failure reusing the existing
  handler. One integration test against a real PostgreSQL container with synthetic
  seeded data proving an actual `SELECT` round-trip.

### Excludes (out of scope, do not touch)

- HRP-85 (search by location/profession) and HRP-86 (statistics endpoint) — their
  own routes, filters and response shapes belong to those tasks.
- HRP-89/HRP-90 (Streamlit frontend) — this task only adds the API route they will
  later call.
- Any schema change (HRP-54), any change to `person_repository.py`'s write path, any
  Docker/Kafka/MongoDB/Redis change.
- A new connection-pooling strategy — reuses `api/db.py`'s existing per-request
  `get_connection` dependency exactly as HRP-83 left it.
- Resolving or asserting real-world person identity. ADR-0006 stays
  `Accepted in principle`; this endpoint returns curated rows matched by exact
  technical field equality, not a claim that they represent one verified real person.

### Open decision this spec must resolve before implementation (human call)

- **Whether `bank_accounts` (`iban`, `salary`) is included in the search response.**
  Unlike `locations`/`professional_profiles`, this table carries financial data.
  Nothing in HRP-24/HRP-25 or `docs/backend-standards.md` explicitly forbids
  exposing it through an authenticated-scope-free internal API, but nothing
  explicitly authorizes it either, and this project has no authentication/authorization
  layer yet (out of scope for every task so far, including HRP-83). **Default
  proposed in this draft: exclude `bank_accounts` from HRP-84's response entirely** —
  it can be added later, deliberately, once an explicit decision (and, if needed, an
  access-control task) approves it. This default must be confirmed or overridden by
  human review before implementation starts, not silently assumed.

## Design

`GET /people/search` is added as another route inside `main.py`'s `create_app()`,
depending on the same `Annotated[psycopg.Connection[...], Depends(get_connection)]`
pattern `/health` already uses. Query parameters are declared as FastAPI/Pydantic
typed parameters so type coercion (e.g. `id` must be an integer) is handled by the
framework; the "at least one filter" and pagination-bounds rules are checked
explicitly in the handler and raise `HTTPException(400, ...)` with a safe, generic
message (no echoed input beyond what the caller already sent as a query string).

The query itself is built with `psycopg.sql.SQL`/`sql.Identifier`/`sql.Placeholder`,
matching `person_repository.py`/`validation_queries.py`'s existing safe-query
convention — never raw string interpolation. Only the filters actually supplied are
included in the `WHERE` clause (`AND`-combined), each bound as a parameter.

Dependent rows (`locations`, `professional_profiles`) are fetched per matched
employee with a second, equally parameterized query, scoped by `employee_id`.

## What stays provisional / unknown / pending

- Whether `bank_accounts` is ever exposed by this or a later endpoint — explicitly
  deferred per the open decision above.
- Any response field or filter implying a resolved, verified real-world identity —
  ADR-0006 remains `Accepted in principle`, not final.
- Authentication/authorization on this or any API route — no task so far has
  introduced one; this remains a known, unaddressed gap for a future task, not
  something HRP-84 silently works around.

## Acceptance criteria

- [ ] `GET /people/search` exists in `api/main.py`, reachable through the existing
      app factory.
- [ ] At least one of `passport`/`first_name`/`last_name`/`id` is required; a request
      with none returns `400`.
- [ ] `limit`/`offset` are validated (bounded, non-negative) and default sensibly.
- [ ] A match returns the employee's curated columns plus its `locations` and
      `professional_profiles` rows; `bank_accounts` is excluded per the open decision
      above (or the spec is updated before implementation if reviewers override it).
- [ ] No match returns an empty result, not an error.
- [ ] Database failures are handled by the existing `psycopg.Error` handler; no new
      logging path is introduced.
- [ ] No HRP-85/86/89/90 logic, no schema/Docker/Kafka/Mongo/Redis change.
- [ ] `docs/specs/HRP-84-search-person-endpoint.md` complete per
      `docs/specs/template.md`.

## Accessibility and sustainability applicability

- Accessibility: not applicable — this is a JSON API response with no rendered
  interface; the Streamlit frontend (HRP-89/90) that will consume it is a separate,
  later task that will assess accessibility for its own UI.
- Sustainability: applicable — bounded pagination (`limit` capped at 100) prevents an
  unbounded query/response; no new persistent connection or background process is
  introduced beyond HRP-83's existing per-request pattern.
- Deferred claims: no performance, throughput or production-readiness claim is made.

## Test strategy

| Nivel | Caso | Evidencia esperada |
|---|---|---|
| Unitario | Match found by each supported filter | `TestClient`, dependency override with fixture rows |
| Unitario | No match | Empty list, `200`, not an error |
| Unitario | No filter supplied | `400`, no query executed |
| Unitario | Invalid `limit`/`offset` | `400` |
| Unitario | Database failure | Reuses the existing handler; `503`, no message leak (same discipline as `/health`'s existing tests) |
| Integración | Real round-trip | Contenedor PostgreSQL real, empleado sintético insertado, `GET` real devuelve las filas esperadas exactas |

## Evidencia de cierre

- Rama / PR: pending
- Commit: pending
- Comandos ejecutados y resultado: pending
- Comentario Jira con el resultado: pending
