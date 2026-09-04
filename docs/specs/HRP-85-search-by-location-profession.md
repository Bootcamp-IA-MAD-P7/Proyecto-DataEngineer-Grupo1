# HRP-85 — Search people by location or profession

**Status:** Draft; implementation authorised — the four open decisions below were
confirmed by Johans Salas (task owner) on 2026-09-04, adopting every proposed
default as-is.
**Owner:** Johans Salas
**Human reviewer:** Miguel or Gaby
**Jira:** HRP-85 — Crear endpoint para consultar personas por ubicación o profesión
**Dependencies:** HRP-83 (API skeleton, merged, Jira: Finalizada); HRP-84 (`GET
/people/search`, merged via PR #64) — no formal "depends on" link in Jira, but
HRP-84's own spec excludes "search by location/profession" as HRP-85's reserved
scope, and this task extends the same module.
**Related ADR:** [`docs/adr/0006-person-correlation-key.md`](../adr/0006-person-correlation-key.md)
**Planned branch:** `feature/HRP-85-search-by-location-profession`

## Objective

Add a second read-only search entry point on top of HRP-83/HRP-84's API, letting a
caller find curated `employees` records by an already-persisted location field
(`locations.city` / `locations.address`) or professional field
(`professional_profiles.job` / `professional_profiles.company`) — matched by exact
value, not a claim of resolved real-world identity.

## Context and scope

### Verified preconditions (checked against `origin/develop` before drafting this spec)

- HRP-83 and HRP-84 are both merged into `develop` (PR [#60](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/60)
  and PR [#64](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/64)).
- Current `src/hr_pro_platform/api/main.py` exposes `create_app()` with `GET
  /health` and `GET /people/search`, both depending on `Annotated[psycopg.Connection[...],
  Depends(get_connection)]` from `api/db.py` — unchanged since HRP-84.
- The actual search logic lives in `src/hr_pro_platform/api/people.py`, not inline in
  `main.py`: `ALLOWED_FILTERS` (a `frozenset` limited to `employees` columns —
  `id`, `passport`, `first_name`, `last_name`), `search_employees()` (builds a
  parameterized `WHERE` clause over **`employees` columns only**, then calls
  `_fetch_dependent()` per matched employee to attach `locations` and
  `professional_profiles` rows), `PersonSearchResult`/`LocationResult`/
  `ProfessionalProfileResult` (Pydantic response models). This is more modular than
  the inline design HRP-84's spec text originally described — this spec follows the
  real code, not the stale description.
- `locations` columns: `full_name`, `city`, `address`, `ip_v4`.
  `professional_profiles` columns: `full_name`, `company`, `company_address`,
  `company_email`, `company_telephone_number`, `job`. (Confirmed in
  `src/hr_pro_platform/storage/postgres.py`; no schema change in this task.)
- No `docs/specs/HRP-85-*.md`, branch or PR existed before this task.
- HRP-85 has one formal Jira blocker, HRP-83, already `Finalizada`. HRP-85 itself
  blocks HRP-90 (Streamlit search UI), which must not start before this is approved.
- ADR-0006 is `Accepted in principle`, not final — unchanged since HRP-84.

### Includes

- A read-only way to search `employees` using `locations.city`, `locations.address`,
  `professional_profiles.job` and/or `professional_profiles.company` as filters,
  returning the same shape HRP-84 already returns (`PersonSearchResult`, including
  its `locations` and `professional_profiles` arrays) for each matching employee.
- At least one filter required (same discipline as HRP-84); a request with none is
  rejected with `400`.
- Bounded response via the same `limit` (default 20, max 100) / `offset` (default
  0) pagination convention as HRP-84.
- Reuse of the existing `psycopg.Error` handler in `main.py` for database failures;
  a separate `400` for invalid filters/pagination, matching HRP-84.
- Unit tests (dependency override, no real database) and one integration test
  against a real PostgreSQL container with synthetic seeded data, mirroring
  `tests/unit/test_api_people_search.py` and `tests/integration/test_api_people_search.py`.

### Excludes (out of scope, do not touch)

- HRP-86 (statistics endpoint) — its own route and response shape.
- HRP-89/HRP-90 (Streamlit frontend) — this task only adds the API route(s) they
  will later call.
- Any schema change (HRP-54, already closed), any change to `person_repository.py`'s
  write path, any Docker/Kafka/MongoDB/Redis change.
- Any change to HRP-84's existing `GET /people/search` filters or response shape —
  this task adds a search path, it does not modify the existing one.
- Any authentication/authorization layer — none exists yet in any task so far; this
  gap stays documented, not silently worked around.
- `bank_accounts` exposure — stays excluded, same as HRP-84, unless a separate,
  explicit human decision authorizes it.
- Resolving or asserting real-world person identity — ADR-0006 stays `Accepted in
  principle`; a match here is exact-equality over curated technical fields, not an
  identity claim.

### Decisions confirmed by human review (Johans Salas, 2026-09-04)

1. **Where the filter lives, architecturally — CONFIRMED: (a).** A new function in
   `people.py` (`search_employees_by_location_or_profession()`) filters
   `locations`/`professional_profiles` first (parameterized, allowlisted columns),
   collects the distinct matching `employee_id`s, then reuses the existing
   per-employee assembly (`employees` row + `_fetch_dependent()` for both tables)
   to build the same `PersonSearchResult` shape. `search_employees()` and
   `ALLOWED_FILTERS` are not modified — lower risk to HRP-84's already-approved,
   already-tested code, at the cost of a second, similar function.
2. **New route vs. extended route — CONFIRMED: a new path,**
   `GET /people/search/by-location-profession`, to avoid conflating two different
   filter-source semantics (and two different "at least one filter" rules) in one
   handler, and to avoid touching HRP-84's already-merged, already-reviewed route.
3. **Filter combination — CONFIRMED: `AND`.** When both a location and a
   profession filter are supplied in the same request (e.g. `city=Madrid&job=Engineer`),
   both must match. The Jira title's "or" describes two available search
   dimensions, not a mandated exclusive-or request shape.
4. **Match semantics — CONFIRMED: exact equality.** No partial/`ILIKE` text search
   in this task, consistent with HRP-84's existing convention; nothing in
   HRP-24/HRP-25/HRP-54 evidences a partial-match requirement. A future task may
   revisit this with its own spec.

## Design

- New route: `GET /people/search/by-location-profession` in `main.py`, alongside
  `/health` and `/people/search`, depending on the same
  `Annotated[psycopg.Connection[...], Depends(get_connection)]` pattern.
- Query parameters: `city`, `address` (from `locations`), `job`, `company` (from
  `professional_profiles`), plus the existing `limit`/`offset` pair. At least one
  of the four is required.
- The new `people.py` function (`search_employees_by_location_or_profession()`)
  first runs a parameterized `SELECT DISTINCT employee_id FROM locations` and/or
  `FROM professional_profiles WHERE <allowlisted filters AND-combined>` (one query
  per source table when filters from both are supplied, the two `employee_id` sets
  then intersected in Python since a single filter never spans both tables), using
  `psycopg.sql.SQL`/`sql.Identifier`/`sql.Placeholder` exactly as
  `search_employees()` already does — never raw string interpolation.
- Matching `employee_id`s are then used to fetch each employee's row and reattach
  its full `locations`/`professional_profiles` arrays via the existing
  `_fetch_dependent()` helper, so the response shape (`PersonSearchResult`) is
  identical to HRP-84's — the caller sees the same object shape regardless of which
  search endpoint found it.
- Pagination (`limit`/`offset`) applies to the distinct-employee result, not to the
  raw `locations`/`professional_profiles` row count, to avoid returning fewer than
  `limit` employees when one employee has multiple matching dependent rows.
- Error handling and the `psycopg.Error` → `503` path are unchanged, reused as-is
  from `main.py`.

## What stays provisional / unknown / pending

- `bank_accounts` exposure — explicitly out of scope here, same as HRP-84.
- Authentication/authorization on this or any API route — still a known,
  unaddressed gap.
- Any response field or filter implying a resolved, verified real-world identity —
  ADR-0006 remains `Accepted in principle`, not final.
- Whether a future task adds partial/`ILIKE` text search — deferred, not decided
  here.

## Acceptance criteria

- [x] The four open decisions above are confirmed by human review before
      implementation starts, and the confirmed choice is recorded in this spec.
- [x] `GET /people/search/by-location-profession` exists accepting `city`,
      `address`, `job` and/or `company` as filters, reachable through the existing
      `create_app()` factory.
- [x] At least one filter is required; a request with none returns `400`.
- [x] `limit`/`offset` are validated (bounded, non-negative) with the same defaults
      as HRP-84.
- [x] A match returns the same `PersonSearchResult` shape HRP-84 already returns
      (including `locations` and `professional_profiles`), for employees found via
      a location or profession match.
- [x] `bank_accounts` remains excluded from every response.
- [x] No match returns an empty list, not an error.
- [x] Database failures are handled by the existing `psycopg.Error` handler; no new
      logging path is introduced.
- [x] HRP-84's existing `GET /people/search` behaviour and response shape are
      unchanged by this task.
- [x] No HRP-86/89/90 logic, no schema/Docker/Kafka/Mongo/Redis change.
- [x] `docs/specs/HRP-85-search-by-location-profession.md` complete per
      `docs/specs/template.md`.

## Accessibility and sustainability applicability

- Accessibility: not applicable — this is a JSON API response with no rendered
  interface; the Streamlit frontend (HRP-89/90) that will consume it is a separate,
  later task that will assess accessibility for its own UI.
- Sustainability: applicable — bounded pagination (`limit` capped at 100) prevents
  an unbounded query/response; no new persistent connection or background process
  is introduced beyond the existing per-request pattern.
- Deferred claims: no performance, throughput or production-readiness claim is
  made.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Unit | Match found by each supported filter (`city`, `address`, `job`, `company`) | `TestClient`, dependency override with fixture rows |
| Unit | Combined filters (e.g. `city` + `job`) apply `AND` | `TestClient`, fixture rows covering both true/false combinations |
| Unit | No match | Empty list, `200`, not an error |
| Unit | No filter supplied | `400`, no query executed |
| Unit | Invalid `limit`/`offset` | `400` |
| Unit | Database failure | Reuses the existing handler; `503`, no message leak |
| Unit | `bank_accounts` never queried | Explicit assertion on rendered SQL, mirroring `test_api_people_search.py` |
| Unit | HRP-84's `GET /people/search` behaviour unchanged | Existing HRP-84 test suite still passes unmodified |
| Integration | Real round-trip | Real PostgreSQL container, synthetic employee(s) with distinguishable location/profession data inserted, `GET` returns the expected exact rows |

## Closing evidence

- Branch: `feature/HRP-85-search-by-location-profession` (created from
  `origin/develop` at `fa156b9`). PR: pending — not opened yet.
- Commit: pending (not committed yet; changes are staged in the working tree only).
- Commands executed and result:
  - `python scripts/validate_specs.py` → passed, 47 specs validated.
  - `python -m ruff check .` → all checks passed.
  - `python -m ruff format --check .` → passed (after auto-formatting the two new
    test files with `python -m ruff format .`).
  - `python -m mypy src` → `Success: no issues found in 32 source files`.
  - `python -m pytest --no-cov` (full suite, no services started) →
    `225 passed, 31 skipped` — the 2 new skips are this task's own integration
    test and `tests/integration/test_api_people_search.py` (both skip cleanly:
    "PostgreSQL is not reachable"), consistent with every other integration test
    in this run when no local Postgres/Mongo/Redis container is running. No real
    PostgreSQL round-trip has been executed yet — the new integration test
    (`tests/integration/test_api_people_search_by_location_profession.py`) is
    unverified against a live database and must be run against
    `infra/compose.dev.yml` before this is considered fully validated.
  - `python -m pre_commit run --all-files` → all hooks passed.
- Human reviewer approval: pending — not requested yet.
- PR not opened; Jira closing comment: pending; closure is not authorised by this
  draft.
