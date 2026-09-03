# HRP-56 — Insert processed person records into PostgreSQL

**Status:** Draft; implementation not yet authorised
**Owner:** Johans Salas
**Human reviewer:** Miguel
**Jira:** HRP-56
**Dependencies:** HRP-54 (PostgreSQL schema, merged); HRP-55 (`PersonRecordMapping`
mapping layer, merged via [PR #49](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/49));
ADR-0006 (`Accepted in principle`)
**Related ADR:** [`docs/adr/0006-person-correlation-key.md`](../adr/0006-person-correlation-key.md)
**Planned branch:** `feature/HRP-56-insert-processed-person-records`

## Objective

Take the candidate rows produced by HRP-55 (`PersonRecordMapping`) and write
them into PostgreSQL for the first time: insert one `employees` row per
component, resolve its database-generated `id`, and use it as `employee_id`
for every dependent-table candidate row belonging to the same component —
without updating existing rows, without deduplicating, and without deciding
any uniqueness or conflict policy that no prior spec or ADR has approved.

## Context and scope

### Verified preconditions (checked against `develop` before drafting this spec)

- `src/hr_pro_platform/storage/person_mapper.py` defines
  `map_person_record(record) -> PersonRecordMapping`, with
  `PersonRecordMapping.employees` / `.locations` / `.professional_profiles` /
  `.bank_accounts` / `.network_data` each a `tuple[CandidateRow, ...]`, and
  `CandidateRow(table, group_key, fields, source_reference)` — confirming
  HRP-55 (PR #49) is merged and stable in `develop`, not only "Finalizada" in
  Jira.
- `src/hr_pro_platform/storage/postgres.py` creates `employees.id` as
  `BIGSERIAL PRIMARY KEY`; no table in `_SCHEMA_STATEMENTS` declares a
  `UNIQUE` constraint on any other column.
- `docs/adr/0006-person-correlation-key.md` status is exactly
  `Accepted in principle`, and its "Responsibility boundaries" section still
  excludes database uniqueness, primary keys, foreign keys and
  `ON CONFLICT`/upsert behaviour from its scope.
- `docs/specs/HRP-55-etl-postgres-connection.md`, section "What stays open",
  still lists `employees.id` persistence identity, business uniqueness and
  `ON CONFLICT`/upsert as unresolved.

### Includes

- A repository layer (proposed location:
  `src/hr_pro_platform/storage/person_repository.py`) that:
  - reuses `PostgresSchemaClient`'s `connect()`/`close()` pattern and
    `storage/config.py` settings — no new connection mechanism;
  - accepts one or more `PersonRecordMapping` values;
  - for each mapping whose `employees` tuple has **exactly one**
    `CandidateRow` (see "Design" below for why this is the only case
    handled), inserts that row with
    `INSERT INTO employees (...) VALUES (...) RETURNING id`, captures the
    generated `id`, and inserts every dependent-table `CandidateRow`
    (`locations`, `professional_profiles`, `bank_accounts`, `network_data`)
    for that mapping with `employee_id` set to that `id`;
  - runs the full set of inserts for one mapping inside a single
    transaction (commit only if every insert in the component succeeds;
    roll back the whole component on any failure);
  - isolates failures per component: one component's insert failure does
    not stop the remaining components from being processed, per
    `docs/backend-standards.md`'s "fail one message safely" rule.
- Explicit, non-silent handling of mappings whose `employees` tuple does
  not have exactly one row (zero, or more than one) — see "Design".
- Unit tests (mocked `psycopg` connection/cursor, no live database) covering
  the insert sequence, correct `employee_id` propagation, transaction
  boundaries, and the skip behaviour for zero/multiple-`employees` mappings.
- One integration test against the real HRP-53 PostgreSQL container,
  skipped automatically when the service is unreachable, reusing the
  `live_connection` fixture pattern from `tests/integration/test_postgres_schema.py`.

### Excludes

- `UPDATE` of existing rows — HRP-57.
- Deduplication or `ON CONFLICT` behaviour — HRP-58. Re-running this
  insertion with the same `ConsolidatedPersonRecord` input will create
  duplicate rows; this is a known, deliberately deferred limitation (see
  "Risks"), not silently prevented here.
- SQL validation queries — HRP-59.
- Verifying already-persisted data — HRP-60.
- Any change to `src/hr_pro_platform/storage/postgres.py`,
  `_SCHEMA_STATEMENTS`, `infra/compose.dev.yml`,
  `src/hr_pro_platform/storage/person_mapper.py`, or any ADR.
- Any business-uniqueness constraint (`UNIQUE` on `passport`, `fullname`,
  `address` or `iban`) — HRP-54 explicitly created none; this task does not
  add one.
- `processing_audit` rows — still out of scope; `correlation_rules` and
  `provenance` remain available on the source `ConsolidatedPersonRecord` for
  a future task to use, but this task does not decide `processing_audit`'s
  content.
- API, frontend, Redis, or any Sprint 5/6 scope.
- Reading, cloning or analysing the educational data generator.

### Verifiable assumptions

- Every `CandidateRow.fields` dict only contains keys that already exist as
  columns in `_SCHEMA_STATEMENTS` (guaranteed by HRP-55's own mapping
  table); this task does not validate that again, it only binds values.
- A component's dependent-table candidate rows may be 0, 1, or many per
  table (e.g. two `locations` rows for one employee) — the existing schema
  already supports this via a plain foreign key with no cardinality
  constraint, so no design decision is needed for that case.

### Risks

- **Duplicate rows on reprocessing:** running this insertion twice for the
  same logical input creates two full sets of rows, because no uniqueness
  or `ON CONFLICT` check exists anywhere in the schema or this task. This is
  accepted and explicitly deferred to HRP-58; it must not be silently
  avoided by inventing an ad hoc check here.
- **Skipped components are not retried or corrected by this task:**
  components without exactly one `employees` candidate row are skipped (see
  "Design"); this task does not implement retry, correction or escalation
  beyond reporting the skip.

## Design

### Resolving `employees.id`

The only implemented sequence is:

```text
INSERT INTO employees (<columns from the CandidateRow.fields keys>)
VALUES (<values>)
RETURNING id
```

The returned `id` becomes `employee_id` on every dependent-table insert for
the same `PersonRecordMapping`. No alternative identity (e.g. `passport` as
a business key) is used, because no spec or ADR has approved one.

### Handling more than one `employees` candidate row (ambiguous personal domain)

`PersonRecordMapping.employees` can contain more than one `CandidateRow`
when the `personal` domain itself is ambiguous (HRP-96: either two distinct
`PersonalGroup`s joined transitively into one component, or one group
already holding conflicting fragments). In that case there is no
approved way to decide which dependent-table candidate row belongs to which
of the several candidate `employees` rows — inventing either a "pick one"
or a "link to all" policy would be a business decision no spec or ADR has
approved.

**Decision:** this task inserts a component **only when its `employees`
tuple has exactly one `CandidateRow`**. Mappings whose `employees` tuple has
zero (no personal-domain contribution) or more than one `CandidateRow` are
skipped entirely — no partial insert, no dependent-only rows, no guessed
`employee_id`. Skipped components are counted and reported (see "Test
strategy" and "Observability"), not silently dropped without any signal.

**Alternative considered and rejected:** inserting one `employees` row per
candidate and linking every dependent row to every one of them (a full
cross-product). Rejected because it would silently invent a many-to-many
association the correlation evidence does not establish, and could make an
unrelated dependent fragment appear linked to an unrelated `employees` row.

### Module boundary

Per `docs/backend-standards.md`, `storage` owns "repository adapters and
idempotent persistence" and "must not contain business decisions." This
task's only business-adjacent decision — skipping ambiguous-personal
components rather than guessing — is documented here explicitly rather than
buried in code, and does not introduce uniqueness, conflict-resolution or
update policy.

## Acceptance criteria

- [ ] `docs/specs/HRP-56-insert-processed-person-records.md` exists, follows
      the template, and links HRP-39, HRP-54, HRP-55 and ADR-0006.
- [ ] The repository layer consumes `PersonRecordMapping`/`CandidateRow`
      from HRP-55 without modifying that module.
- [ ] `employees.id` is resolved via `INSERT ... RETURNING id` and correctly
      propagated as `employee_id` to every dependent-table insert for the
      same component.
- [ ] All inserts for one component run inside a single transaction
      (all-or-nothing).
- [ ] A failure in one component does not prevent other components from
      being processed.
- [ ] Components whose `employees` tuple does not have exactly one
      `CandidateRow` are skipped and reported, never partially inserted.
- [ ] No `UPDATE`, `ON CONFLICT` or duplicate-check logic is introduced.
- [ ] The duplicate-on-reprocessing risk is documented explicitly (this
      spec, "Risks").
- [ ] `postgres.py`, `_SCHEMA_STATEMENTS`, `infra/compose.dev.yml`,
      `person_mapper.py` and ADR-0006 remain unmodified.
- [ ] Unit tests use a mocked connection/cursor; no unit test opens a live
      PostgreSQL connection.
- [ ] One integration test runs against a real HRP-53 PostgreSQL container
      and is skipped automatically when it is unreachable.
- [ ] No payload, PII, secret, `.env` value or generator reference appears
      anywhere in this change.

## Accessibility and sustainability applicability

- Accessibility: not applicable. No user-facing flow, UI component or
  rendered interface is introduced.
- Sustainability: applicable in a limited sense, per `docs/base-standards.md`
  §6. Inserts happen once per component per invocation with no polling; the
  known duplicate-on-reprocessing risk is documented rather than hidden
  behind unapproved retry/dedup logic that would add complexity without
  review.
- Deferred claims: none.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Unit | A mapping with exactly one `employees` row inserts it and propagates the returned `id` to every dependent row | Mocked cursor asserts `INSERT`/`RETURNING` call and subsequent `employee_id` bind values |
| Unit | All inserts for one component run inside one transaction; a failure rolls back the whole component | Mocked connection asserts `commit()`/`rollback()` calls |
| Unit | A mapping with zero `employees` rows is skipped, not partially inserted | Mocked cursor receives no `INSERT` calls for that mapping |
| Unit | A mapping with more than one `employees` row (ambiguous personal domain) is skipped, not cross-linked | Mocked cursor receives no `INSERT` calls for that mapping |
| Unit | A component's dependent table with multiple candidate rows (e.g. two `locations`) inserts each one with the same `employee_id` | Mocked cursor asserts one `INSERT` per candidate row, same `employee_id` bind value |
| Unit | A failure in one component does not stop processing of the next component | Mocked connection raises for one component, second component still receives its inserts |
| Integration | Real insert against the HRP-53 container round-trips through `information_schema`/`SELECT` | `tests/integration/test_person_repository.py`, skipped automatically if PostgreSQL is unreachable, reusing the `live_connection` fixture pattern |
| Quality | `pre-commit run --all-files`, `ruff check .`, `ruff format --check .`, `mypy src`, `pytest`, `python scripts/validate_specs.py` | Commands pass |
| Human review | Miguel reviews that no uniqueness, update or conflict-resolution decision was smuggled in, and that the ambiguous-personal skip behaviour is acceptable | Approval recorded in the PR before any next step |

## Closing evidence

- Branch / PR: `feature/HRP-56-insert-processed-person-records` / pending.
- Commit: pending.
- Commands executed and result: pending.
- Human reviewer approval: pending.
- Jira closing comment: pending; closure is not authorised by this draft.
