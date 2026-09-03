# HRP-57 — Update records when new data arrives

**Status:** Draft; implementation not yet authorised
**Owner:** Johans Salas
**Human reviewer:** Miguel
**Jira:** HRP-57
**Dependencies:** HRP-51 (`incomplete -> complete` transformation transitions,
merged); HRP-56 (`PersonRepository`, merged); HRP-58 (source-reprocessing
idempotency via `processing_audit`, merged via [PR #51](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/51));
ADR-0006 (`Accepted in principle`)
**Related ADR:** [`docs/adr/0006-person-correlation-key.md`](../adr/0006-person-correlation-key.md)
**Planned branch:** `feature/HRP-57-update-records-on-new-data`

## Objective

Allow a component whose `employees` candidate row's `source_reference` was
already recorded in `processing_audit` (HRP-58) to contribute genuinely new
dependent-table data (`locations`, `professional_profiles`, `bank_accounts`,
`network_data`) to its existing `employees.id` on a later reprocessing pass,
instead of being skipped wholesale as HRP-58 does today — without resolving
person-identity, without deduplicating dependent rows that already exist,
and without deciding an `UPDATE` policy for `employees`' own columns that no
spec or ADR has approved.

## Context and scope

### Verified preconditions (checked against `develop` before drafting this spec)

- `src/hr_pro_platform/storage/person_repository.py` defines
  `PersonRepository.insert_mapping()`, `_already_processed()` and
  `_record_processing_audit()`, and `processing_audit`
  (`employee_id`, `stage`, `status`, `raw_event_ref`, `occurred_at`) is a
  real, populated table — confirming HRP-56 and HRP-58 (PR #51, merged
  after three rounds of review) are stable in `develop`, not only
  "Finalizada" in Jira.
- `docs/specs/HRP-58-avoid-duplicate-records.md`, section "Risks", states:
  *"A component's `source_reference` reappearing with new/enriched
  dependent fragments is currently skipped entirely, not merged ... Handling
  that enrichment case is HRP-57's responsibility."* This task closes
  exactly that documented gap.
- `docs/adr/0006-person-correlation-key.md` status is exactly
  `Accepted in principle`; its "Responsibility boundaries" section still
  excludes database uniqueness and an approved business-identity key.
- The technical unique index `ix_processing_audit_raw_event_ref` proposed by
  HRP-58 is present in `_SCHEMA_STATEMENTS`.

### Why this scenario is real, not hypothetical

`docs/specs/HRP-51-handle-incomplete-duplicate-order.md` already defines
that the transformation layer supports `incomplete -> complete` transitions
as additional valid evidence arrives for the *same* underlying Personal
fragment. Concretely: the same `employees` candidate row (same
`source_reference`, same `passport`/`name`/`last_name`) can be consolidated
today with fewer dependent domains than it will be tomorrow, once more raw
fragments correlate with it. HRP-58's idempotency check treats that second,
richer consolidation as "already processed" and discards the new dependent
data entirely. This task is what lets that new data actually reach
PostgreSQL.

### Includes

- A precise definition of "new dependent data" for this task: given a
  component whose `employees` candidate row's `source_reference` is already
  recorded in `processing_audit`, a dependent `CandidateRow` (in
  `locations`, `professional_profiles`, `bank_accounts` or `network_data`)
  counts as new if no existing row for that `employee_id` in that table has
  the exact same field values. Exact match only — no fuzzy comparison, no
  precedence rule (see "What stays open").
- Extending `PersonRepository.insert_mapping()`'s control flow (not
  `_already_processed()` or `_record_processing_audit()` themselves, which
  stay exactly as HRP-58 left them) so that when the check finds a match:
  1. resolve the existing `employee_id` for that `source_reference` from
     `processing_audit` — never from a business-identity field;
  2. for each dependent `CandidateRow` in the incoming mapping, check
     whether an identical row already exists for that `employee_id`; insert
     only the ones that do not;
  3. if at least one new dependent row was inserted, mark the enrichment on
     `processing_audit` by **updating** the existing row's `stage`/`status`
     (e.g. to `stage="update"`, `status="enriched"`) — not by inserting a
     second row. HRP-58's proposed unique index on `raw_event_ref` allows at
     most one `processing_audit` row per source reference, so a second
     `INSERT` for the same `source_reference` would violate it (confirmed
     against a live database during implementation: this was not a
     hypothetical concern). This `UPDATE` targets only `processing_audit`'s
     own bookkeeping columns — never `employees` or any dependent table — so
     it does not conflict with the "no `UPDATE` policy for `employees`'s own
     columns" exclusion below;
  4. all of the above inside one transaction per component, following the
     same commit/rollback/logging discipline `insert_mapping()` already
     uses for the insert path.
- Explicit, non-silent reporting of what happened: "genuinely nothing new"
  (no dependent row differed) stays reported the way HRP-58 already reports
  it; "new dependent data was added" must be distinguishable from both a
  fresh `employees` insert and a no-op skip, so a caller (and tests) can
  tell them apart.
- Unit tests (mocked, no live database) covering: a component with new
  dependent data enriches the existing `employee_id`; a component with no
  new dependent data behaves exactly as HRP-58's existing skip; no code
  path in this feature ever reads or compares a business-identity field.
- One integration test against the real HRP-53 PostgreSQL container,
  skipped automatically when unreachable, with cleanup scoped to the
  `employee_id` values the test itself created — per the lesson from
  HRP-58's third review round, never by a fixed reference string.

### Excludes

- Any business-identity key or uniqueness — still not approved.
- `UPDATE` of `employees`' own columns (`first_name`, `passport`, `sex`,
  etc.) when they differ on reprocessing. Left as an open question (see
  "What stays open"), not implemented.
- Deduplication logic itself — that is HRP-58's, already merged; this task
  only extends what happens *after* HRP-58's check finds a match, it does
  not change the check.
- SQL validation queries — HRP-59.
- Verifying already-persisted data — HRP-60.
- Any change to `src/hr_pro_platform/storage/person_mapper.py`,
  `_already_processed()`, `_record_processing_audit()` as they exist today,
  `infra/compose.dev.yml`, or any ADR.
- Any recency/precedence rule (last-write-wins, offset-wins, timestamp-wins)
  — explicitly prohibited by ADR-0006 and HRP-51 alike.
- API, frontend, Redis, or any Sprint 5/6 scope.
- Reading, cloning or analysing the educational data generator.

### Verifiable assumptions

- `processing_audit.employee_id` is populated by HRP-58's
  `_record_processing_audit()` for every successful insert, so the existing
  `employee_id` for an already-processed `source_reference` can always be
  recovered from that table without guessing.
- Dependent tables have no cardinality limit per `employee_id` (confirmed in
  HRP-52/HRP-54): inserting an additional `locations` row for an existing
  employee is already a structurally valid operation today, nothing about
  the schema needs to change for this task.

### Risks

- **Exact-match "new data" detection can miss near-duplicates.** A
  dependent row that differs by even one character (e.g. a corrected
  `city`) is treated as entirely new evidence and inserted alongside the
  old one, not as a correction. This is consistent with the project's
  existing "no silent merge, no invented conflict resolution" principle
  (HRP-96, HRP-51) but means an employee can accumulate multiple `locations`
  rows over time from what a human might consider "the same place,
  corrected." No precedence or correction logic is introduced to change
  this.
- **This task does not update `employees`' own columns.** If the same
  `source_reference` reappears with a different `email`, that change is
  silently not reflected in `employees` — this is an explicit limitation
  (see "What stays open"), not an oversight.
- **Additional `processing_audit` rows accumulate per enrichment event.**
  This grows the audit table proportionally to reprocessing frequency; no
  retention/cleanup policy is defined here (out of scope, consistent with
  `processing_audit` having no such policy today either).

## Design

### Module boundary

Per `docs/backend-standards.md`, `storage` "must not contain business
decisions." Detecting "does an identical dependent row already exist for
this employee_id" is a technical equality check, not a business decision —
it does not decide who a person is, only whether this exact fragment's
dependent data was already persisted. This keeps HRP-57 inside the same
boundary HRP-55/56/58 already established.

### Enrichment flow

```text
insert_mapping(mapping)
  -> source_reference = mapping.employees[0].source_reference
  -> existing_employee_id = lookup via processing_audit (HRP-58's table)
  -> if not found: proceed exactly as HRP-56/58 already do (fresh insert)
  -> if found:
       for each dependent CandidateRow in the incoming mapping:
         -> exists = SELECT 1 FROM <table> WHERE employee_id = existing_employee_id
                      AND <every field> = <candidate value> LIMIT 1
         -> if not exists: insert it, linked to existing_employee_id
       -> if any row was inserted: UPDATE the existing processing_audit row
          in place (stage="update", status="enriched") -- not a 2nd INSERT,
          which HRP-58's proposed unique index on raw_event_ref forbids
       -> if no row was inserted: report exactly as HRP-58's existing skip
          (no processing_audit write, no employees/dependent write)
       all within one transaction for the component
```

This only ever inserts new dependent rows; it never issues `UPDATE` or
`DELETE` against `employees` or any dependent table.

## What stays open (provisional / unknown / pending)

- **`employees`' own column changes** (e.g. `email`, `telephone_number`
  differing on reprocessing) — not handled by this task; left for a future,
  separately reviewed decision.
- **Near-duplicate / correction detection** for dependent rows (e.g.
  correcting a typo in `city`) — exact match only; no fuzzy/normalized
  comparison is introduced.
- **Recency or precedence policy** for any future conflict resolution — not
  decided here, and not decidable without an approved business/version
  field, consistent with ADR-0006 and HRP-51.
- **Retention policy for accumulating `processing_audit` rows** — not
  addressed by this task.

## Acceptance criteria

- [ ] `docs/specs/HRP-57-update-records-on-new-data.md` exists, follows the
      template, and links HRP-39, HRP-51, HRP-56, HRP-58 and ADR-0006.
- [ ] "New dependent data" is defined precisely as exact-value absence for
      the existing `employee_id`, with no fuzzy comparison.
- [ ] The existing `employee_id` is resolved via `processing_audit`, never
      via a business-identity field.
- [ ] Only genuinely new dependent `CandidateRow`s are inserted; existing
      ones are never duplicated, updated, or deleted.
- [ ] No `UPDATE` of `employees`' own columns is introduced.
- [ ] No recency/precedence rule is introduced.
- [ ] `_already_processed()` and `_record_processing_audit()` remain exactly
      as HRP-58 left them; `person_mapper.py`, `infra/compose.dev.yml` and
      ADR-0006 remain unmodified.
- [ ] A component with no new dependent data behaves exactly as HRP-58's
      existing skip (no spurious writes, no spurious audit rows).
- [ ] Unit tests use a mocked connection/cursor; no unit test opens a live
      PostgreSQL connection.
- [ ] One integration test runs against a real HRP-53 PostgreSQL container,
      skipped automatically when unreachable, with cleanup scoped to the
      `employee_id` values it creates.
- [ ] No payload, PII, secret, `.env` value or generator reference appears
      anywhere in this change.

## Accessibility and sustainability applicability

- Accessibility: not applicable. No user-facing flow, UI component or
  rendered interface is introduced.
- Sustainability: applicable in a limited sense, per `docs/base-standards.md`
  §6. The enrichment check adds one bounded `SELECT` per dependent candidate
  row against an indexed foreign key (`employee_id`); no new service,
  polling, or unbounded retention is introduced beyond the already-accepted
  growth of `processing_audit`.
- Deferred claims: none.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Unit | A component with an already-recorded `source_reference` and one genuinely new dependent row inserts only that row, linked to the existing `employee_id` | Mocked cursor asserts one dependent `INSERT` with the existing `employee_id` bound, and an additional `processing_audit` insert |
| Unit | A component with an already-recorded `source_reference` and no new dependent data performs no write at all | Mocked cursor receives no `INSERT` calls |
| Unit | The existing-employee lookup and the "does this row already exist" check never bind a business-identity field | Assert bound values only ever include `source_reference`/`employee_id`/dependent-table fields already approved by HRP-25 |
| Unit | `_already_processed()`/`_record_processing_audit()` call sites and behaviour are unchanged from HRP-58 | Existing HRP-58 tests continue to pass unmodified |
| Integration | Insert a component, reprocess it with one additional dependent fragment, confirm exactly one new row appears and the original is untouched | Real HRP-53 container, skipped automatically if unreachable; cleanup scoped to the `employee_id`s created |
| Quality | `pre-commit run --all-files`, `ruff check .`, `ruff format --check .`, `mypy src`, `pytest`, `python scripts/validate_specs.py` | Commands pass |
| Human review | Miguel reviews that no business-identity resolution, `UPDATE` policy, or recency rule was smuggled in | Approval recorded in the PR before any next step |

## Closing evidence

- Branch / PR: `feature/HRP-57-update-records-on-new-data` / pending.
- Commit: pending.
- Commands executed and result: pending.
- Human reviewer approval: pending.
- Jira closing comment: pending; closure is not authorised by this draft.
