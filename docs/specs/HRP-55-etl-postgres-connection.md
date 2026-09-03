# HRP-55 — Connect the ETL process to PostgreSQL

**Status:** Draft; implementation not yet authorised
**Owner:** Johans Salas
**Human reviewer:** Miguel
**Jira:** HRP-55
**Dependencies:** HRP-54 (PostgreSQL schema, merged); HRP-53 (PostgreSQL Docker
service, merged); HRP-50 / HRP-96 / HRP-51 (`ConsolidatedPersonRecord` contract,
merged); ADR-0006 (`Accepted in principle`)
**Related ADR:** [`docs/adr/0006-person-correlation-key.md`](../adr/0006-person-correlation-key.md)
**Planned branch:** `feature/HRP-55-etl-postgres-connection`

## Objective

Define a repository/mapping layer that translates a `ConsolidatedPersonRecord`
(the output of `transformation.person_consolidator.consolidate_person_records`,
HRP-50/HRP-96/HRP-51) into candidate rows for the six curated PostgreSQL tables
already created by HRP-54, without executing any write against the database and
without deciding any persistence-identity, uniqueness or conflict-resolution
policy that no prior spec or ADR has approved.

This specification does not implement `INSERT`, `UPDATE` or `ON CONFLICT`
behaviour. It prepares the input those future tasks (HRP-56, HRP-57, HRP-58)
will consume.

## Context and scope

### Verified preconditions (checked against `develop` before drafting this spec)

- `src/hr_pro_platform/storage/postgres.py` — `PostgresSchemaClient` creates the
  six curated tables (`employees`, `locations`, `professional_profiles`,
  `bank_accounts`, `network_data`, `processing_audit`) via `create_schema()`.
- `infra/compose.dev.yml` defines the `postgres` service (`postgres:16`).
- `src/hr_pro_platform/transformation/person_consolidator.py` defines
  `consolidate_person_records(...) -> ConsolidationResult`, with
  `ConsolidationResult.records: tuple[ConsolidatedPersonRecord, ...]`.
- `docs/adr/0006-person-correlation-key.md` status is exactly
  `Accepted in principle`, and its "Responsibility boundaries" section
  explicitly excludes database uniqueness, primary keys, foreign keys and
  `ON CONFLICT`/upsert behaviour from its scope.

### Includes

- A pure mapping function/module (proposed location:
  `src/hr_pro_platform/storage/person_mapper.py`) that:
  - accepts one `ConsolidatedPersonRecord`;
  - returns a candidate-row representation for each of the six curated tables,
    using only the columns already declared in `postgres.py`'s
    `_SCHEMA_STATEMENTS` (no new column is introduced);
  - does not assign a primary-key value (`id` is `BIGSERIAL`, database-assigned
    at insert time — out of this task's control) and does not decide how
    `employee_id` foreign keys resolve to a concrete `employees.id`;
  - preserves `correlation_rules` and `provenance` from the source record
    alongside the candidate rows, so HRP-56 can carry that traceability into
    `processing_audit` if it chooses to.
- Explicit, documented behaviour for `complete`, `incomplete` and `ambiguous`
  consolidated records at the mapping level: this task maps all three the same
  way (structural translation only); it does not decide whether an
  `incomplete` or `ambiguous` record should be written, skipped or flagged —
  that decision belongs to HRP-56/HRP-57.
- A connection-reuse note: the mapper does not open its own database
  connection; it is a pure, side-effect-free transformation. Any future
  `connect()`/`close()` needed to actually persist reuses
  `PostgresSchemaClient`'s existing pattern (HRP-56's responsibility).
- Unit tests (mocked, no live PostgreSQL) covering the mapping for `complete`,
  `incomplete` and `ambiguous` records, including domains with multiple
  `DomainGroupContribution` entries (post-HRP-96 ambiguity shape).

### Excludes

- Executing `INSERT`, `UPDATE` or `UPSERT` against PostgreSQL — HRP-56 and
  HRP-57.
- Deduplication or `ON CONFLICT` behaviour — HRP-58.
- SQL validation queries — HRP-59.
- Verifying already-persisted data — HRP-60.
- Any change to `src/hr_pro_platform/storage/postgres.py`,
  `_SCHEMA_STATEMENTS`, or `infra/compose.dev.yml` (HRP-53/HRP-54 remain
  authoritative and unmodified).
- Any change to `docs/adr/0006-person-correlation-key.md` or its status.
- Deciding the persistence semantics of a global `person_id`, a business
  uniqueness constraint, or `ON CONFLICT` precedence.
- API, frontend, Redis, or any Sprint 5/6 scope.
- Reading, cloning or analysing the educational data generator.

### Verifiable assumptions

- The observed-field-to-curated-column mapping is already approved in
  `docs/specs/HRP-25-modelo-datos.md` (e.g. `employees.telephone_number` ←
  observed `telfnumber`; `bank_accounts.iban` ← observed `IBAN`;
  `professional_profiles.company_address` ← observed `company address`;
  `network_data.ip_v4` / `locations.ip_v4` ← observed `IPv4`). This task reuses
  that mapping; it does not redefine it.
- `GroupedFragment.payload` (from `fragment_contract.py`) carries the raw,
  observed field names listed above — not the curated column names — so the
  mapper is responsible for the field-name translation, not a schema change.
- No table in `_SCHEMA_STATEMENTS` declares a `UNIQUE` constraint (confirmed in
  HRP-54); the mapper therefore cannot rely on database-level conflict
  detection and must not simulate one.

### Risks

- `employees.id` is database-generated (`BIGSERIAL`); this task cannot
  pre-assign it, so any `employee_id` foreign-key value on dependent-table
  candidate rows remains unresolved until HRP-56 defines how/when an
  `employees` row is created or matched. This is documented as an open
  decision, not silently resolved here.
- Cardinality between `employees` and its dependent tables when a
  `ConsolidatedPersonRecord` domain contains more than one
  `DomainGroupContribution` (an `ambiguous` record, per HRP-96) is not decided
  by this task; the mapper must represent every group's candidate rows without
  collapsing or picking one.

## Design

### Module boundary

Per `docs/backend-standards.md`, `storage` owns "repository adapters and
idempotent persistence" and "must not contain business decisions." This task
stays inside that boundary: `person_mapper.py` is a pure function from
`ConsolidatedPersonRecord` to candidate rows, with no database I/O, no
decision about whether/when to write, and no invented uniqueness or conflict
rule.

### Field mapping (per domain, reusing HRP-25's approved column mapping)

| Domain | Curated table | Candidate row fields |
|---|---|---|
| `personal` | `employees` | `first_name` ← `name`, `last_name` ← `last_name`, `sex`, `telephone_number` ← `telfnumber`, `email`, `passport` |
| `location` | `locations` | `full_name` ← `fullname`, `city`, `address`, `ip_v4` ← `IPv4` |
| `professional` | `professional_profiles` | `full_name` ← `fullname`, `company`, `company_address` ← `company address`, `company_email`, `company_telephone_number` ← `company_telfnumber`, `job` |
| `bank` | `bank_accounts` | `iban` ← `IBAN`, `passport`, `salary` |
| `net` | `network_data` | `ip_v4` ← `IPv4` |

Each candidate row also carries the originating `DomainGroupContribution.key`
and every contributing `GroupedFragment.source_reference`, so downstream tasks
can populate `processing_audit.raw_event_ref` without re-deriving provenance.

A record with multiple `DomainGroupContribution` entries in one domain (the
`ambiguous` case, HRP-96) produces one candidate row **per group**, not a
merged row — matching HRP-96's rule that group boundaries must not be
flattened.

### What stays open (provisional / unknown / pending)

- **Persistence identity:** how/when an `employees.id` is created or matched
  for a given consolidated record. Not decided here; flagged for HRP-56.
- **Business uniqueness:** whether `passport`, `fullname`, `address` or `iban`
  should ever back a `UNIQUE` constraint. HRP-54 explicitly created none;
  this task does not propose one.
- **`ON CONFLICT`/upsert behaviour:** entirely deferred to HRP-58, per
  ADR-0006's responsibility boundaries.
- **Write policy for `incomplete`/`ambiguous` records:** whether they are
  written as partial rows, held back, or flagged — deferred to HRP-56/HRP-57.
- **Cardinality** between `employees` and dependent tables when more than one
  `DomainGroupContribution` exists per domain — deferred, consistent with
  HRP-25's own `pending` marking on this point.

## Acceptance criteria

- [ ] A pure mapping function/module translates `ConsolidatedPersonRecord`
      into candidate rows for all six curated tables, using only columns
      already defined by HRP-54.
- [ ] The mapping for each domain matches the observed-field-to-column
      correspondence already approved in `docs/specs/HRP-25-modelo-datos.md`.
- [ ] `complete`, `incomplete` and `ambiguous` records are all mapped
      structurally, with no decision about whether to persist them.
- [ ] A record with multiple `DomainGroupContribution` entries in one domain
      produces one candidate row per group (no flattening).
- [ ] `correlation_rules` and `provenance`/`source_reference` are preserved
      alongside the candidate rows.
- [ ] No `employees.id` or other primary-key value is assigned by this task.
- [ ] No `INSERT`, `UPDATE`, `UPSERT` or `ON CONFLICT` statement is introduced.
- [ ] `postgres.py`, `_SCHEMA_STATEMENTS`, `infra/compose.dev.yml` and
      ADR-0006 remain unmodified.
- [ ] Unit tests use mocked/synthetic data only; no test opens a live
      PostgreSQL connection.
- [ ] No payload, PII, secret, `.env` value or generator reference appears
      anywhere in this change.

## Accessibility and sustainability applicability

- Accessibility: not applicable. No user-facing flow, UI component or
  rendered interface is introduced.
- Sustainability: applicable in a limited sense, per `docs/base-standards.md`
  §6. The mapper is a pure, in-memory transformation with no new dependency,
  no polling, no additional persistence or network transfer of its own — it
  only prepares data for a write that a later task performs.
- Deferred claims: none.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Unit | `complete` record maps to one candidate row per table | Mocked `ConsolidatedPersonRecord` fixture |
| Unit | `incomplete` record maps missing domains to no candidate row (not a fabricated empty one) | Mocked fixture |
| Unit | `ambiguous` record with 2 `DomainGroupContribution` in one domain maps to 2 candidate rows for that domain | Mocked fixture, mirrors HRP-96's own ambiguity test |
| Unit | `correlation_rules` and `source_reference` values are carried into the mapping output unchanged | Mocked fixture |
| Unit | No test opens a live PostgreSQL connection or executes SQL | Code review / no `psycopg` calls outside `postgres.py` |
| Quality | `pre-commit run --all-files`, `ruff check .`, `ruff format --check .`, `mypy src`, `pytest`, `python scripts/validate_specs.py` | Commands pass |
| Human review | Miguel reviews that no persistence-identity or uniqueness decision was smuggled in | Approval recorded in the PR before any next step |

## Closing evidence

- Branch / PR: `feature/HRP-55-etl-postgres-connection` / pending.
- Commit: pending.
- Commands executed and result: pending.
- Human reviewer approval: pending.
- Jira closing comment: pending; closure is not authorised by this draft.
