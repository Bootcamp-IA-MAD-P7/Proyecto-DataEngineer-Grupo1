# HRP-54 — Create tables, primary keys, foreign keys and indexes

**Status:** Draft; implementation authorised
**Owner:** Johans
**Human reviewer:** Miguel
**Jira:** HRP-54
**Dependencies:** HRP-52 (table/relationship design, merged) and HRP-53 (PostgreSQL Docker service, merged)
**Related ADR:** `docs/adr/0002-raw-and-curated-storage.md`, `docs/adr/0006-person-correlation-key.md`
**Planned branch:** `feature/HRP-54-postgres-schema`

## Objective

Create the real PostgreSQL schema — tables, primary keys, candidate foreign keys
and indexes — exactly as designed in `docs/specs/HRP-52-tablas-relaciones.md`,
against the engine already provisioned by HRP-53. Schema creation must be
idempotent, contain no unauthorised business rule, and not assume any cardinality
that `docs/adr/0006-person-correlation-key.md` has not approved.

## Context and scope

### Includes

- A `storage` module (`src/hr_pro_platform/storage/`) that connects to PostgreSQL
  and creates the six curated tables from HRP-52
  (`employees`, `locations`, `professional_profiles`, `bank_accounts`,
  `network_data`, `processing_audit`) using `CREATE TABLE IF NOT EXISTS`.
- The candidate primary keys, foreign keys, `ON DELETE` behaviour, and indexes
  exactly as listed in HRP-52's "Foreign keys and indexes per table" table.
- The column set and proposed types from `docs/specs/HRP-25-modelo-datos.md`,
  with explicit, documented defaults for the two columns HRP-25 left as `pending`
  (`sex`, `salary`) and the ambiguous `TEXT`-or-`INET` choice for `ip_v4`.
- Environment configuration for the storage module
  (`src/hr_pro_platform/storage/config.py`), reusing the `POSTGRES_*` variables
  already declared in `.env.example` by HRP-53.
- Unit tests (mocked) and a real integration test against the HRP-53 container,
  skipped automatically when PostgreSQL is not reachable (matching CI, which does
  not start Docker services yet).

### Excludes

- Any ETL, correlation or business logic that decides what data to insert — that
  is HRP-55, which remains blocked on Gaby's correlation work (HRP-43/44/45).
- Any API or query code — that is the Sprint 6 API tasks.
- A definitive person-correlation key, uniqueness constraint, or assumed
  cardinality between `employees` and its dependent tables — `docs/adr/0006-person-correlation-key.md`
  remains `Proposed` and this task does not change that status.
- An exhaustive SQL persistence test suite — `docs/specs/HRP-70-*.md` (not yet
  written) owns that; this task's tests only verify that the schema exists and
  respects HRP-52's constraints.
- Any migration framework (e.g. Alembic) — see "Schema-creation mechanism" below.
- Any reading, cloning or inspection of the educational data generator.

### Verifiable assumptions

- `docs/specs/HRP-52-tablas-relaciones.md` and `docs/specs/HRP-25-modelo-datos.md`
  are merged into `develop` and are the only sources of table, column, key and
  index definitions used here.
- `infra/compose.dev.yml`'s `postgres` service (HRP-53, merged) is the target
  engine; this task does not modify that service.
- `docs/adr/0006-person-correlation-key.md` is `Proposed`, not `Accepted`.
- The project has no ORM or migration framework yet.
  `src/hr_pro_platform/ingestion/mongo.py` (HRP-33) sets a precedent: connect to
  the database driver directly (`pymongo`, no ODM) and create indexes
  idempotently inside `connect()`-adjacent code, logged and tested the same way
  as any other adapter.

### Risks

- `CREATE TABLE IF NOT EXISTS` does not alter an existing table whose columns
  already diverge from this definition. That is an acceptable risk for a
  brand-new, empty database and is documented here rather than silently assumed;
  a schema-evolution/migration strategy is deferred until real data exists.
- Storing `sex` as `JSONB` and `salary`/`ip_v4` as `TEXT` (see below) may need to
  change once their formats are confirmed. Both are reversible column-type
  changes, not business rules, so they do not require an ADR.

## Design

### Schema-creation mechanism (spec-level decision, not ADR-level)

**Decision:** no ORM, no migration framework. `src/hr_pro_platform/storage/postgres.py`
defines `PostgresSchemaClient`, mirroring `MongoIngestionClient`'s `connect()`/`close()`
shape, with a `create_schema()` method that runs a fixed, ordered tuple of
`CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS` statements inside one
transaction.

**Why:** the project already has a working precedent (MongoDB's idempotent index
creation in application code) and explicitly favours the smallest justified
dependency set (`docs/base-standards.md` §6, ADR-0007). Introducing Alembic now
would add a dependency and a versioned-migration workflow before there is any
real data or schema-evolution need to justify it. This is reversible: a migration
framework can be introduced later, in its own task, once the schema needs to
evolve against non-empty tables.

**Driver:** `psycopg` v3 (`psycopg[binary]`), the direct equivalent of `pymongo`
for PostgreSQL — no ORM layer, consistent with the existing MongoDB adapter style.

### Column-type defaults for previously `pending` fields

| Column | HRP-25 status | Chosen type here | Why (reversible, not a business rule) |
|---|---|---|---|
| `employees.sex` | `pending` (observed as a JSON array) | `JSONB` | Preserves the observed array shape exactly; does not force an enum or normalise unknown values |
| `bank_accounts.salary` | `pending` (`NUMERIC` candidate; observed as string) | `TEXT` | Preserves the observed string shape; avoids inventing a numeric format, currency, or rounding rule not evidenced by HRP-29 |
| `locations.ip_v4`, `network_data.ip_v4` | `TEXT` or `INET` | `TEXT` | `INET` would reject any value that is not strictly valid, which HRP-29 never validated; `TEXT` accepts the data as observed |
| `processing_audit.raw_event_ref` | `pending` (format: `ObjectId` string vs. `topic/partition/offset` triple) | `TEXT` | Accepts either representation without forcing a structure ahead of that decision |

All four are documented, reversible implementation defaults. None encodes a
business rule, a correlation key, or a required/optional/nullable constraint that
`docs/02-data-contract.md` leaves as unknown.

### Nullability defaults

- Every table's `id` is `NOT NULL` (implicit via `PRIMARY KEY`).
- `employees.created_at` / `employees.updated_at` and `processing_audit.occurred_at`
  are `NOT NULL DEFAULT now()`: they are platform-generated audit timestamps, not
  business content.
- `employee_id` is `NOT NULL` on `locations`, `professional_profiles`,
  `bank_accounts` and `network_data`: these tables exist specifically to depend on
  an employee, so an ownerless row would be meaningless referential state, not a
  business-content decision. `processing_audit.employee_id` stays nullable, per
  HRP-52's explicit note that an audit entry may exist before a curated employee
  record does.
- No other column is marked `NOT NULL`: `docs/02-data-contract.md` leaves
  required/optional/nullable as an open unknown for observed business fields, so
  this task does not invent one.

### Foreign keys, `ON DELETE` behaviour and indexes

Implemented exactly as candidate in `docs/specs/HRP-52-tablas-relaciones.md`:
`fk_locations_employees`, `fk_professional_profiles_employees`,
`fk_bank_accounts_employees`, `fk_network_data_employees` all `ON DELETE CASCADE`;
`fk_processing_audit_employees` nullable, `ON DELETE SET NULL`. Every foreign key
has a matching non-unique support index
(`ix_<table>_employee_id`), plus `ix_processing_audit_occurred_at` for audit
queries, per HRP-52. No unique index exists on `passport`, `fullname`, `address`
or `iban` anywhere in the schema.

### Module boundaries

`src/hr_pro_platform/storage/` only creates and owns schema; it contains no
correlation, classification or upsert logic (`docs/backend-standards.md`:
storage "Must not: Contain business decisions"). `PostgresSchemaClient` is
intentionally free of any reference to Kafka, MongoDB, or a specific "person"
concept — HRP-55 will build a repository layer on top of this schema without
needing to change it.

## Acceptance criteria

- [ ] `src/hr_pro_platform/storage/postgres.py` creates all six tables from
      HRP-52, with the exact candidate primary keys, foreign keys, `ON DELETE`
      behaviour, and indexes.
- [ ] No `UNIQUE` constraint exists anywhere in the created schema.
- [ ] Running schema creation twice against the same database does not error and
      does not duplicate objects (idempotency).
- [ ] `docker compose -f infra/compose.dev.yml up -d postgres` plus running the
      schema-creation code produces the six tables, verifiable via
      `information_schema` (real evidence, not only unit-test mocks).
- [ ] Unit tests cover connection, schema creation, and the "no unique business
      constraint" invariant using mocks, consistent with the existing MongoDB
      test style.
- [ ] The spec documents the schema-creation mechanism decision and the four
      previously-`pending` column-type defaults, with justification.
- [ ] No ETL, correlation, upsert or API code is introduced.
- [ ] `pyproject.toml` declares the new PostgreSQL driver dependency.
- [ ] No payload, PII, secret or generator reference appears anywhere in this
      change.

## Accessibility and sustainability applicability

- Accessibility: not applicable. No implemented user-facing flow, UI component or
  rendered interface is introduced.
- Sustainability: applicable in a limited sense, per `docs/05-test-harness.md`'s
  rule that work affecting Docker/data stores documents applicable efficiency
  evidence. Schema creation is a one-shot, idempotent set of DDL statements
  executed once at startup, not a polling or repeated-write pattern; it adds no
  new service, only two small support indexes per dependent table. No
  container-resource measurement is claimed.
- Deferred claims: none.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Unit | `connect()` opens a connection and probes it with `SELECT 1` | Mocked `psycopg.connect`, `tests/unit/test_postgres_schema.py` |
| Unit | `create_schema()` executes every statement and commits once | Mocked cursor/connection |
| Unit | The schema statements contain no `UNIQUE` keyword | String assertion over `_SCHEMA_STATEMENTS` |
| Unit | `close()` closes the connection, and is a no-op when never connected | Mocked connection |
| Integration | Real schema creation against the HRP-53 container is idempotent (run twice) and produces exactly the six expected tables | `tests/integration/test_postgres_schema.py`, skipped automatically if PostgreSQL is unreachable |
| Integration | No dependent table has a `UNIQUE` constraint on any column | `information_schema.table_constraints` query |
| Integration | `locations` references `employees` through `fk_locations_employees` | `information_schema.constraint_column_usage` query |
| Quality | `pre-commit run --all-files`, `ruff check .`, `ruff format --check .`, `mypy src`, `pytest`, `python scripts/validate_specs.py` | Commands pass |
| Human review | Miguel reviews the schema diff for coherence with HRP-52 and the MongoDB precedent | Approval recorded in the PR before any next step |

## Closing evidence

- Branch / PR: `feature/HRP-54-postgres-schema` / pending.
- Commit: pending.
- Commands executed and result: pending.
- Human reviewer approval: pending.
- Jira closing comment: pending; closure is not authorised by this draft.
