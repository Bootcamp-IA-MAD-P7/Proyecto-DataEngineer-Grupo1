# HRP-58 — Avoid duplicate records

**Status:** Draft; implementation not yet authorised; schema-change proposal pending human review
**Owner:** Johans Salas
**Human reviewer:** Miguel
**Jira:** HRP-58
**Dependencies:** HRP-54 (PostgreSQL schema, merged); HRP-55 (`PersonRecordMapping`,
merged); HRP-56 (`PersonRepository`, merged via [PR #50](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/50));
ADR-0006 (`Accepted in principle`)
**Related ADR:** [`docs/adr/0006-person-correlation-key.md`](../adr/0006-person-correlation-key.md)
**Planned branch:** `feature/HRP-58-avoid-duplicate-records`

## Objective

Prevent reprocessing the same source event from producing duplicate rows in
PostgreSQL, without inventing a business-identity uniqueness key (`passport`,
`fullname`, `address`, `iban`) that no spec or ADR has approved for
persistence.

## Context and scope

### Verified preconditions (checked against `develop` before drafting this spec)

- `src/hr_pro_platform/storage/person_repository.py` defines
  `PersonRepository.insert_mapping()` / `.insert_mappings()`, confirming
  HRP-56 (PR #50) is merged and stable.
- `src/hr_pro_platform/storage/postgres.py` still creates `processing_audit`
  (`id`, `employee_id`, `stage`, `status`, `raw_event_ref`, `occurred_at`)
  with no `UNIQUE` constraint on any column, and neither `person_mapper.py`
  nor `person_repository.py` inserts into it yet.
- `docs/adr/0006-person-correlation-key.md` status is exactly
  `Accepted in principle`; its "Responsibility boundaries" section still
  excludes "database uniqueness" and "ON CONFLICT/upsert behavior" from its
  scope, and no approved business identity key exists.
- `docs/specs/HRP-56-insert-processed-person-records.md`, section "Risks",
  still documents reinserting the same `ConsolidatedPersonRecord` as a known,
  deliberately deferred duplication risk.

### Two different meanings of "duplicate" (do not conflate them)

1. **Person-identity duplicate** ("is this the same real person already
   stored?"). Still has no approved key. ADR-0006 is explicit that its four
   correlation edges are a provisional operational strategy, not proof of
   real-world identity, and that it does not decide PostgreSQL business
   uniqueness. **Out of scope for HRP-58.**
2. **Source-reprocessing duplicate** ("have I already inserted this exact
   fragment before?"). This is a technical idempotency problem, analogous to
   the `topic + partition + offset` idempotency `docs/backend-standards.md`
   already defines for Kafka/MongoDB raw ingestion. The equivalent here is
   `GroupedFragment.source_reference` / `CandidateRow.source_reference`
   (HRP-55), which already reaches `person_repository.py` unused. **This is
   what HRP-58 addresses.**

### Includes

- Idempotency tracking via the existing, currently-unused
  `processing_audit` table: before inserting a component, check whether its
  employee candidate row's `source_reference` was already recorded; if so,
  skip the insert and report it explicitly (mirroring
  `InsertOutcome.skipped_reason` from HRP-56).
- On a successful insert, record one `processing_audit` row per inserted
  component (`employee_id`, `stage="insert"`, `status="inserted"`,
  `raw_event_ref=<employees candidate row's source_reference>`), so the next
  reprocessing attempt can detect it.
- **Schema-change proposal (separate, explicit, pending approval — not
  applied silently):** to make the idempotency check race-safe and enforced
  at the database level rather than only at the application level, this spec
  proposes adding
  `CREATE UNIQUE INDEX IF NOT EXISTS ix_processing_audit_raw_event_ref ON processing_audit (raw_event_ref) WHERE raw_event_ref IS NOT NULL`
  to `_SCHEMA_STATEMENTS`. This is a **technical** uniqueness constraint on
  an opaque, non-PII source reference — not a business-identity constraint
  on `passport`/`fullname`/`address`/`iban` — so it does not fall under
  ADR-0006's exclusion of business uniqueness. It still requires Miguel's
  explicit sign-off before merge, exactly like any other schema change
  (`docs/backend-standards.md`: "Schema changes require a spec update").
- Unit tests (mocked, no live database) covering: a new component inserts
  normally and records a `processing_audit` row; a component whose
  `source_reference` is already recorded is skipped, not re-inserted; the
  skip check never references a business-identity field.
- One integration test against the real HRP-53 PostgreSQL container, skipped
  automatically when unreachable, reusing the pattern from
  `tests/integration/test_person_repository.py`.

### Excludes

- Any business-uniqueness key (`passport`, `fullname`, `address`, `iban`) on
  `employees` or any dependent table.
- `UPDATE` of existing rows — HRP-57.
- SQL validation queries — HRP-59.
- Verifying already-persisted data — HRP-60.
- Any change to `src/hr_pro_platform/storage/person_mapper.py`, the parts of
  `person_repository.py` unrelated to deduplication, `infra/compose.dev.yml`,
  or any ADR.
- Resolving real person identity or the cardinality between `employees` and
  its dependent tables.
- API, frontend, Redis, or any Sprint 5/6 scope.
- Reading, cloning or analysing the educational data generator.

### Verifiable assumptions

- Every candidate `employees` row inserted by `PersonRepository` carries a
  `source_reference` (guaranteed by `CandidateRow`, HRP-55); this task reuses
  it rather than deriving a new identifier.
- `processing_audit.raw_event_ref` is `TEXT`, nullable, with no existing
  constraint — adding a partial unique index (`WHERE raw_event_ref IS NOT
  NULL`) does not reject any row this project currently writes, since no
  writer path populates that column yet.

### Risks

- **Two different fragments could, in principle, carry the same
  `source_reference` if the upstream contract does not guarantee
  uniqueness.** `docs/specs/HRP-55-etl-postgres-connection.md`'s provenance
  contract requires a `SourceReference` to "identify one source fragment
  deterministically and unambiguously," but this has not been verified
  end-to-end against real Kafka/MongoDB provenance. This task treats that
  contract as trustworthy, consistent with HRP-55/HRP-56, and does not
  re-verify it.
- **What to do when the same `source_reference` reappears with different
  field content** (a genuine conflict, not a pure replay) is left as an open
  question — see "What stays open" below. This task only handles the exact
  case of "already recorded, skip"; it does not compare content.
- **The proposed unique index only prevents the race at the database level
  for future concurrent writers.** The application-level pre-check
  (`SELECT` before `INSERT`) is not itself race-free without it; this
  asymmetry is documented, not silently resolved by adding transactional
  locking or `ON CONFLICT` handling beyond the index itself.
- **A component's `source_reference` reappearing with new/enriched
  dependent fragments is currently skipped entirely, not merged.** If the
  same Personal fragment is reprocessed alongside a newly-arrived `location`
  fragment that was not present the first time, this task still skips the
  whole component once its `source_reference` is recorded — the new
  dependent data is not captured. Handling that enrichment case is HRP-57's
  responsibility (updating existing records when new data arrives), not
  this task's.
- **A concurrent uniqueness conflict currently surfaces as a rollback and a
  raised/propagated error, not as `skipped_reason="already_processed"`.**
  If the proposed index is approved and two writers race past the
  application-level check, the loser's `processing_audit` insert (or a
  future `employees`-level conflict) fails with a database uniqueness
  error; `insert_mapping()` rolls back and re-raises it, and
  `insert_mappings()` records it as `skipped_reason="insert_error"`, not
  `"already_processed"`. Distinguishing "lost the race" from "other
  insert failure" is not implemented by this task.
- **Reverting this commit does not remove an index already created on a
  live PostgreSQL database.** `_SCHEMA_STATEMENTS` only ever adds
  (`CREATE ... IF NOT EXISTS`); there is no down-migration. If the proposed
  index is approved, deployed, and later needs to be removed, that requires
  a separate, explicit `DROP INDEX` change — reverting the code change alone
  leaves the index in place on any database it already ran against.

## Design

### Module boundary

Per `docs/backend-standards.md`, `storage` "must not contain business
decisions." Checking a technical, upstream-supplied `source_reference` for
prior processing is not a business decision — it does not decide who a
person is, only whether this exact fragment was already handled. This keeps
HRP-58 inside the same boundary HRP-55/56 already established.

### Idempotency check flow

```text
insert_mapping(mapping)
  -> source_reference = mapping.employees[0].source_reference
  -> SELECT 1 FROM processing_audit WHERE raw_event_ref = %s
  -> if found: skip, report skipped_reason="already_processed"
  -> if not found: proceed with the existing HRP-56 insert sequence,
     then INSERT INTO processing_audit (employee_id, stage, status, raw_event_ref)
     VALUES (<new employee_id>, 'insert', 'inserted', <source_reference>)
     inside the same transaction as the component's other inserts
```

This only applies to components HRP-56 would otherwise insert (exactly one
`employees` candidate row). Components already skipped by HRP-56 (zero or
ambiguous personal domain) are unaffected by this task.

## What stays open (provisional / unknown / pending)

- **Person-identity uniqueness / business key** — still not approved by any
  spec or ADR.
- **`UPDATE` of existing rows** — HRP-57.
- **Conflicting content under the same `source_reference`** (same reference,
  different field values on reprocessing): not addressed here. This task
  only detects "already recorded", it does not compare payload content: that
  requires an explicit conflict-resolution contract this project does not
  yet have.
- **The proposed unique index itself** — pending Miguel's explicit approval
  before merge; not applied unilaterally by this task.

## Candidate person-identity keys for a future ADR revision (proposal only — not decided, not implemented)

Johans asked whether this task could also propose a person-identity key.
That decision is explicitly outside this project's AI-authorship boundary
(`AGENTS.md`: "A human approves ... architecture decisions") and outside
ADR-0006's current evidence: HRP-43's investigation concluded
**"Insufficient evidence"** for a universal person key, and ADR-0006 states
"absence of observed collisions is not evidence of uniqueness." Nothing
below is applied by this task — no `UNIQUE` constraint, no `ON CONFLICT`
clause, no code path treats any of these as authoritative.

For Miguel's consideration only, if the team wants to reopen that
investigation:

| Candidate | Basis | Known risk (already documented in ADR-0006 / HRP-43) |
|---|---|---|
| `employees.passport` | Used today as the `personal_bank_passport` operational correlation edge; 397 observed one-to-one matches (HRP-43) | Bounded-sample evidence only; no guarantee of global uniqueness or that two different people never share a value in the real data source |
| `employees.passport` + `locations.full_name` composite | Chains the `personal_location_fullname` edge | Composite candidates were explicitly rejected in HRP-43 for "no identity-grounded evidence"; would need new evidence, not reuse of existing operational edges |
| A generated technical `person_id` decoupled from any observed field | Avoids business-field coupling entirely | Does not solve deduplication on its own — still requires a correlation rule to decide when two inserts refer to "the same" `person_id`, which is the same open question |

None of these should be adopted without a new authorised Kafka observation
(beyond HRP-29/HRP-43's bounded sample) and a human-reviewed ADR-0006
revision, per that ADR's own "Required evidence before acceptance" section.

## Acceptance criteria

- [ ] `docs/specs/HRP-58-avoid-duplicate-records.md` exists, follows the
      template, and links HRP-39, HRP-54, HRP-55, HRP-56 and ADR-0006.
- [ ] The spec explicitly distinguishes person-identity duplicates (out of
      scope) from source-reprocessing duplicates (in scope).
- [ ] Deduplication is based on `source_reference`/`processing_audit`, never
      on a person-identity field.
- [ ] The proposed unique index on `raw_event_ref` is documented as a
      separate, explicit schema-change proposal pending Miguel's approval,
      not applied silently as part of the same change.
- [ ] An already-processed component is skipped and reported explicitly,
      never partially inserted.
- [ ] No `UPDATE`, validation query, or business-identity resolution is
      introduced.
- [ ] `person_mapper.py`, `infra/compose.dev.yml` and ADR-0006 remain
      unmodified.
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
  §6. Avoiding duplicate inserts directly reduces unnecessary storage growth
  from reprocessing; the added `SELECT` per component is a small, bounded
  cost against an indexed column once the proposed index is approved.
- Deferred claims: none.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Unit | A new component (unseen `source_reference`) inserts normally and records a `processing_audit` row | Mocked cursor asserts the `processing_audit` `INSERT` with the correct `raw_event_ref` |
| Unit | A component whose `source_reference` is already recorded is skipped, not re-inserted | Mocked cursor returns an existing row for the `SELECT`; no `employees`/dependent `INSERT` calls follow |
| Unit | The skip check never queries or compares a business-identity field | Assert the `SELECT`/`INSERT` bound values only ever include `source_reference`/`raw_event_ref`, never `passport`/`fullname`/etc. |
| Unit | The `processing_audit` insert happens inside the same transaction as the component's other inserts | Mocked connection asserts a single `commit()` covering both |
| Integration | A real insert followed by a real reprocessing attempt of the same input inserts once and skips the second time | `tests/integration/test_person_repository.py`-style test, skipped automatically if PostgreSQL is unreachable |
| Quality | `pre-commit run --all-files`, `ruff check .`, `ruff format --check .`, `mypy src`, `pytest`, `python scripts/validate_specs.py` | Commands pass |
| Human review | Miguel reviews and explicitly approves (or rejects) the proposed unique index before merge | Approval recorded in the PR before any next step |

## Closing evidence

- Branch / PR: `feature/HRP-58-avoid-duplicate-records` / pending.
- Commit: pending.
- Commands executed and result: pending.
- Human reviewer approval: pending.
- Jira closing comment: pending; closure is not authorised by this draft.
