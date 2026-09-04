# HRP-83 — PostgreSQL query API skeleton

**Status:** Draft; not yet implemented
**Owner:** Johans Salas
**Human reviewer:** Miguel or Gaby
**Jira:** HRP-83 — Crear API para consultar PostgreSQL
**Dependencies:** HRP-54 (PostgreSQL schema, merged); HRP-55/56/57/58 (`person_mapper`/
`PersonRepository`, merged); HRP-59 (`validation_queries`, merged); HRP-60 (grouped-data
persistence verification, merged)
**Related ADR:** [`docs/adr/0006-person-correlation-key.md`](../adr/0006-person-correlation-key.md)
**Planned branch:** `feature/HRP-83-postgres-query-api`

## Objective

Provide the minimal, documented FastAPI skeleton — application factory, PostgreSQL
connection dependency, common error handling, and a single health endpoint — that
HRP-84, HRP-85, HRP-86 (business endpoints) and HRP-89 (Streamlit frontend) can build
on, without implementing any of their business logic here.

## Context and scope

### Verified preconditions (checked against `develop` before drafting this spec)

- No `docs/specs/HRP-83-*.md`, branch or PR existed before this task.
- HRP-83 has no open Jira blocker of its own; it blocks HRP-84, HRP-85, HRP-86 and
  HRP-89 (all still `Tareas por hacer`), which is the correct build order.
- The persistence layer this API will read is stable and merged:
  `src/hr_pro_platform/storage/postgres.py` (schema), `person_repository.py`
  (write path), `validation_queries.py` (read-only checks, 6 functions confirmed
  present).
- `src/hr_pro_platform/api/` contains only an empty `__init__.py`; `pyproject.toml`
  declares no `fastapi`/`uvicorn`/ASGI dependency yet — this is a greenfield addition,
  not a migration.

### Includes

- `fastapi` and an ASGI server (`uvicorn[standard]`) added to `[project.dependencies]`
  in `pyproject.toml`; `httpx` added to the `dev`/test dependency group (required by
  FastAPI's `TestClient`).
- `src/hr_pro_platform/api/main.py`: the FastAPI application factory/instance.
- `src/hr_pro_platform/api/db.py`: a request-scoped PostgreSQL connection dependency,
  reusing `storage/config.py`'s existing `POSTGRES_*` environment variables — no new
  configuration surface.
- Common error handling: a database error is caught and logged with only
  `type(error).__name__` and `error.sqlstate` (mirroring `person_repository.py`'s
  existing logging discipline), never the exception message, and turned into a safe,
  generic JSON error response.
- One functional route: `GET /health` (or `/healthz`), which executes `SELECT 1`
  against PostgreSQL and reports `ok`/`unavailable` — the only business-shaped
  response this task produces, used purely to prove the skeleton actually connects.
- Unit tests using FastAPI's `TestClient` covering the health endpoint's success and
  database-unavailable paths (dependency override, no real database required), plus
  one integration test proving the skeleton connects to a real PostgreSQL container.

### Excludes (out of scope, do not touch)

- Any HRP-84/85/86 business endpoint (search by person, by location/profession,
  statistics) — their request/response contracts, query design and tests belong to
  those tasks, not this one.
- The HRP-89 Streamlit frontend.
- Any change to the PostgreSQL schema (HRP-54), Docker, Kafka, MongoDB or Redis.
- Any change to `person_repository.py`'s write path or `validation_queries.py`'s
  existing functions — the API only reads through them or through new read-only
  queries scoped to `/health`.
- Resolving or exposing a person correlation/identity key — ADR-0006 stays
  `Accepted in principle`, not final; no endpoint in this task returns person data at
  all.

## Design

`src/hr_pro_platform/api/main.py` creates the FastAPI app and registers the health
route. `db.py` exposes a FastAPI dependency (`Depends`) that opens a `psycopg`
connection per request using the same `POSTGRES_HOST`/`PORT`/`DB`/`USER`/`PASSWORD`
variables `storage/config.py` already validates, and closes it after the request —
no new connection-pooling design is introduced in this task (a pool is a reasonable
follow-up once real query endpoints exist, not before). Per `docs/backend-standards.md`
("API additions"), this spec is written and reviewed before any FastAPI code exists.

Per `docs/01-architecture.md`'s responsibility table, the API's contract is
"controlled queries over curated data → JSON" and explicitly excludes transforming
events — this task's only functional output (`/health`) does not touch business data
at all, keeping the skeleton itself uncontroversial with respect to that boundary.

## What stays provisional / unknown / pending

- The concrete shape of every business endpoint (HRP-84/85/86) — deferred entirely to
  those tasks.
- Any response field derived from person correlation is out of scope until ADR-0006
  is no longer provisional; this task returns no person data.
- Connection pooling / lifespan-managed pool: left as a follow-up once real query
  endpoints exist; `/health`'s per-request connection is sufficient for this skeleton.

## Acceptance criteria

- [ ] `fastapi` and an ASGI server are added to `pyproject.toml` with a justification
      for each in the PR description.
- [ ] `src/hr_pro_platform/api/main.py` exposes a FastAPI app importable and runnable
      via the added ASGI server.
- [ ] `GET /health` returns a safe `ok` response when PostgreSQL is reachable and a
      safe (non-leaking) `unavailable` response when it is not — verified against a
      real PostgreSQL container, not only a mocked dependency.
- [ ] No database error message, only `type(error).__name__`/`sqlstate`, ever reaches
      a log line or an HTTP response body.
- [ ] No HRP-84/85/86/89 business logic, no schema/Docker/Kafka/Mongo/Redis change.
- [ ] `docs/specs/HRP-83-postgres-query-api.md` complete per `docs/specs/template.md`.

## Accessibility and sustainability applicability

- Accessibility: not applicable — this task exposes no user-facing interface; the
  Streamlit frontend (HRP-89) is a separate, later task that will assess it.
- Sustainability: applicable — a per-request connection with no long-lived pool keeps
  this skeleton's footprint minimal until real query load exists; no new external
  service or polling loop is introduced.
- Deferred claims: no performance, throughput or production-readiness claim is made
  by this skeleton.

## Test strategy

| Nivel | Caso | Evidencia esperada |
|---|---|---|
| Unitario | `GET /health` returns `ok` when the DB dependency succeeds | `TestClient`, dependency override, no real database |
| Unitario | `GET /health` returns a safe `unavailable` response when the DB dependency raises, and only `type(error).__name__`/`sqlstate` is logged | `TestClient`, dependency override raising a `psycopg` error, `caplog` asserts no message text |
| Integración | The API skeleton actually connects to a real PostgreSQL container | Contenedor real (`infra/compose.dev.yml`), `GET /health` returns `ok` |

## Evidencia de cierre

- Rama: `feature/HRP-83-postgres-query-api`; PR: pending
- Commit: pending (se añade tras el commit final de implementación)
- Comandos ejecutados y resultado:
  - `pre-commit run --all-files` → passed
  - `ruff check .` / `ruff format --check .` → passed
  - `mypy src` → `Success: no issues found in 31 source files`
  - `pytest` (suite completa contra PostgreSQL real,
    `docker compose -f infra/compose.dev.yml up -d postgres`) →
    `221 passed, 2 skipped in 23.63s` (skips son solo MongoDB, no relacionados)
  - Arranque real con el servidor ASGI:
    `python -m uvicorn hr_pro_platform.api.main:app --host 127.0.0.1 --port 8123`
    + `curl http://127.0.0.1:8123/health` → `{"status":"ok"}` — confirma que el
    esqueleto arranca de verdad, no solo vía `TestClient`.
- Comentario Jira con el resultado: pending (se redacta tras aprobación de PR)
