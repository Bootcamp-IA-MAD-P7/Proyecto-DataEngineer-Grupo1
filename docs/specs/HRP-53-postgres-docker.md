# HRP-53 — Create PostgreSQL via Docker

**Status:** Draft; implementation authorised
**Owner:** Johans
**Human reviewer:** Miguel
**Jira:** HRP-53
**Dependencies:** None formal in Jira; independent of HRP-52 (see below); builds on the MongoDB Compose pattern from HRP-33
**Related ADR:** `docs/adr/0002-raw-and-curated-storage.md`, `docs/adr/0004-configuration-and-secrets.md`
**Planned branch:** `feature/HRP-53-postgres-docker`

## Objective

Provide a reproducible, local PostgreSQL service via Docker Compose, following the
same pattern already established by MongoDB in HRP-33. The service must start
empty and healthy, with configuration supplied through environment variables. This
task provisions the database engine; it does not create tables, schemas or
business data.

## Context and scope

### Includes

- A `postgres` service added to the existing `infra/compose.dev.yml`, alongside the
  existing `mongo` service, without modifying `mongo`.
- A named volume for PostgreSQL data, matching the `mongo_data` pattern.
- A healthcheck using `pg_isready` against the configured database and user.
- Any missing environment variable needed to connect to the service
  (`POSTGRES_HOST`, `POSTGRES_PORT`), added to `.env.example` with non-sensitive
  placeholder values, consistent with `POSTGRES_DB`, `POSTGRES_USER` and
  `POSTGRES_PASSWORD`, which already existed as reserved variables.
- Documentation updates in `infra/README.md`, `docs/07-runbook.md` and the root
  `README.md` describing how to start, verify and stop the service, and correcting
  the two status rows that become stale once this service exists.

### Excludes

- SQL DDL, migrations, table creation, primary/foreign keys or indexes — that is
  HRP-54, which formalises `docs/specs/HRP-52-tablas-relaciones.md` into real
  schema objects.
- The full Docker Compose stack with the application and MongoDB integrated
  together — that is HRP-63.
- ETL, API or any application code that connects to PostgreSQL.
- Any reading, cloning or inspection of the educational data generator.
- Any real secret, credential or production endpoint. `.env.example` only ever
  carries non-sensitive placeholder values; the actual `.env` stays local and
  untracked, per ADR-0004.

### Verifiable assumptions

- HRP-53 has no formal "depends on" link in Jira.
- HRP-53 does not depend on HRP-52: `docs/specs/HRP-52-tablas-relaciones.md`
  (merged into `develop`) explicitly states "HRP-53 (Docker) is independent and may
  proceed in parallel" — an empty PostgreSQL engine does not need an approved table
  design.
- Two sibling tasks already merged into `develop` bound this task's scope without
  overlapping it: HRP-62 (`docs/specs/HRP-62-application-dockerfile.md`) explicitly
  excludes "Docker Compose, MongoDB, PostgreSQL, Redis, Prometheus, or any other
  service"; HRP-64 (`docs/specs/HRP-64-environment-configuration.md`) explicitly
  excludes "new... Docker services". Neither already covers this service.
- `infra/compose.dev.yml` currently defines only the `mongo` service (HRP-33,
  owned by Anahí); this task adds `postgres` alongside it using the same
  conventions (`container_name`, `restart: unless-stopped`, a
  `127.0.0.1`-only published port, a named volume, a healthcheck).
- HRP-53 is a child of HRP-39 and blocks HRP-63 in Jira; HRP-63 should not
  integrate PostgreSQL into the full application Compose until this service exists
  and is verified healthy.

### Risks

- Docker Compose resolves `.env` relative to the compose file's own directory by
  default, not the caller's working directory. Verified empirically: plain `${VAR}`
  substitution in `infra/compose.dev.yml` would silently resolve to an empty string
  even with a root `.env` present. The `postgres` service therefore uses
  `env_file: [{path: ../.env, required: false}]` instead of `${VAR}` substitution,
  so it reads the same root `.env` the `mongo` workflow already assumes, and does
  not fail `docker compose config` when `.env` does not exist (e.g. in CI).
- A `postgres:16` major-version tag was chosen instead of MongoDB's
  major-minor style (`mongo:7.0`) because floating major-version tags are the
  idiomatic, commonly used convention for the official PostgreSQL image; this is a
  reversible implementation default, not an architecture decision.

## Design

### Compose service

```yaml
postgres:
  image: postgres:16
  container_name: hr-pro-postgres-dev
  restart: unless-stopped
  env_file:
    - path: ../.env
      required: false
  ports:
    - "127.0.0.1:5432:5432"
  volumes:
    - postgres_data:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U \"$$POSTGRES_USER\" -d \"$$POSTGRES_DB\""]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 10s
```

`$$` escapes the `$` so Compose passes a literal `$POSTGRES_USER`/`$POSTGRES_DB` to
the container's shell at healthcheck time, where `env_file` has already set those
as real container environment variables — not a Compose-file-level substitution,
which would require `.env` to exist at parse time.

### Environment variables

| Variable | Status before this task | Status after this task |
|---|---|---|
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Declared in `.env.example`, unused by any service or code | Consumed by the new `postgres` service via `env_file`; still unconsumed by application code |
| `POSTGRES_HOST`, `POSTGRES_PORT` | Did not exist | Added to `.env.example` (`localhost`, `5432`) documenting the local connection endpoint; not consumed by any service yet (the container reads its own internal port, not these variables) |

No variable carries a real secret. `POSTGRES_PASSWORD` keeps its existing
non-sensitive placeholder (`change-me-locally`).

### Why this does not touch HRP-52 or HRP-54

Starting an empty PostgreSQL engine requires a database name, a user and a
password — none of which encode a business rule, a correlation key or a table
schema. Nothing in this design creates a table, a constraint or an index. HRP-54
formalises the schema from `docs/specs/HRP-52-tablas-relaciones.md` against this
running engine once that design is reviewed.

## Acceptance criteria

- [ ] `infra/compose.dev.yml` defines a `postgres` service without modifying the
      existing `mongo` service.
- [ ] `docker compose -f infra/compose.dev.yml config --quiet` passes with no local
      `.env` present.
- [ ] `docker compose -f infra/compose.dev.yml up -d postgres` starts a container
      that reaches a healthy state via `pg_isready`.
- [ ] No table, schema, extension or SQL statement is created anywhere in this
      change.
- [ ] `.env.example` only adds non-sensitive placeholder values.
- [ ] `infra/README.md`, `docs/07-runbook.md` and the root `README.md` describe how
      to start, verify and stop the service, consistent with the existing MongoDB
      instructions.
- [ ] No payload, PII, secret or generator reference appears anywhere in this
      change.

## Accessibility and sustainability applicability

- Accessibility: not applicable. This task has no implemented user-facing flow, UI
  component or rendered interface.
- Sustainability: applicable, per `docs/05-test-harness.md`'s rule that Docker work
  documents applicable efficiency evidence. This service runs as a single
  container with a bounded, named volume, published only on `127.0.0.1` (no
  external exposure), and default resource limits from the base `postgres:16`
  image — no replication, no extra sidecar process, and no unbounded log or data
  retention beyond the developer's own local disk. No container-resource
  measurement (CPU/memory ceiling) is claimed; only the design choices that bound
  its footprint are documented.
- Deferred claims: none. No accessibility conformance, carbon, energy or
  deployment claim is made by this spec.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Static | `docker compose -f infra/compose.dev.yml config --quiet` with no local `.env` | Command exits 0 |
| Static | `docker compose -f infra/compose.dev.yml config --quiet` with a local `.env` copied from `.env.example` | Command exits 0 |
| Runtime | `docker compose -f infra/compose.dev.yml up -d postgres` then `docker compose -f infra/compose.dev.yml ps` | `postgres` container reports `healthy` |
| Runtime | `docker compose -f infra/compose.dev.yml exec -T postgres pg_isready -U hr_pro -d hr_pro` | Returns `accepting connections` |
| Security | Inspect the diff for `.env` content, credentials or payload data | None present |
| Documentary | `python scripts/validate_specs.py` and `pre-commit run --all-files` | Commands pass with no unrelated changes |
| Human review | Miguel reviews the Compose diff and documentation for coherence with the MongoDB pattern from HRP-33 | Approval recorded in the PR before any next step |

## Closing evidence

- Branch / PR: `feature/HRP-53-postgres-docker` / pending.
- Commit: pending.
- Commands executed and result: pending.
- Human reviewer approval: pending.
- Jira closing comment: pending; closure is not authorised by this draft.
