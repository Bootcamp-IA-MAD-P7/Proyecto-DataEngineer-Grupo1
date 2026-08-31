# Task packet — HRP-52

**Status:** Draft
**Owner:** Johans
**Human reviewer:** Miguel
**Jira:** HRP-52
**Spec:** `docs/specs/HRP-52-tablas-relaciones.md`
**Planned branch:** `feature/HRP-52-tablas-relaciones`

## Expected outcome

A documented, human-reviewable relational design for the PostgreSQL tables already
proposed in HRP-25: candidate primary keys, candidate foreign keys, candidate
technical indexes and a naming convention, without fixing a business correlation key
and without writing SQL.

## Authorised context

- Briefing / document: Jira task HRP-52, child of HRP-39.
- Relevant local documentation: `docs/specs/HRP-25-modelo-datos.md`,
  `docs/03-data-model.md`, `docs/adr/0002-raw-and-curated-storage.md`,
  `docs/adr/0006-person-correlation-key.md`.
- Observed Kafka evidence (if applicable): the same evidence already recorded by
  HRP-24/HRP-29; no new observation was performed for HRP-52.
- Related decisions or ADRs: ADR-0002, ADR-0006 (remains `Proposed`).

## Dependencies and limits

- Depends on: HRP-25 (merged, PR #18/#19). No formal "depends on" link exists in
  Jira, but Miguel's comment on HRP-52 requires coherence with the global data
  model.
- Does not include: creating real tables, SQL, migrations, Docker or ETL — those
  belong to HRP-54 and HRP-53. HRP-54 depends on this reviewed design; HRP-53 is an
  independent Docker enablement task and may proceed in parallel.
- Risk or unknown: the real cardinality between `employees` and its dependent
  tables, pending ADR-0006.
- Constraint: do not read, clone or analyse the educational data generator.

## Request to the assistant

**Role:** Data architecture reviewer/designer (serving-engineer).
**Concrete question:** Does the key/index design formalise HRP-25 without fixing a
cardinality or uniqueness rule that ADR-0006 has not approved?
**Expected output format:** per-entity key/index tables, a candidate relationship
diagram and an explicit list of what remains pending.
**Evaluation criteria:** coherence with HRP-25, no invented business rules, Miguel's
review.

## Human review of the result

- [ ] Facts and assumptions are separated.
- [ ] Cited paths and references exist.
- [ ] No field, topic or Kafka behaviour is invented.
- [ ] The proposal respects scope and security constraints.
- [ ] The result has been applied or discarded, with a stated reason.

## AI usage log

- Tool / role: Claude Code, data architecture reviewer/designer role
  (serving-engineer).
- Date: 2026-08-31.
- Summary of output: formalised candidate primary keys, candidate foreign keys,
  technical indexes and a naming convention for the PostgreSQL tables already
  proposed in HRP-25, in `docs/specs/HRP-52-tablas-relaciones.md`, without resolving
  the person-correlation key (ADR-0006 remains `Proposed`).
- Human decision: pending.
- Reviewer: Miguel (review pending).
