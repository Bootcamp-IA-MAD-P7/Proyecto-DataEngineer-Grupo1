# Task packet — HRP-25

**Status:** Draft
**Owner:** Johans
**Human reviewer:** Gaby
**Jira:** HRP-25
**Specification:** `docs/specs/HRP-25-*.md`
**Planned branch:** `feature/HRP-25-modelo-datos`

## Expected outcome

Define a MongoDB/PostgreSQL model proposal that preserves raw events, temporary
state, and traceable, idempotent curated records, validated against the available
contract.

## Authorised context

- Briefing / assignment: MongoDB, SQL, and person-level aggregation requirements.
- Relevant local documentation: `docs/01-architecture.md`,
  `docs/02-data-contract.md`, and `docs/03-data-model.md`.
- Observed Kafka evidence, where applicable: HRP-29 evidence and HRP-24
  consolidation.
- Related decisions or ADRs: ADR-0001, ADR-0002, and ADR-0003.

## Dependencies and boundaries

- Depends on HRP-23 and HRP-24; HRP-24 depends on HRP-29.
- Does not include final table creation or persistence implementation.
- Risks / unknowns: canonical identity, cardinalities, and final data types.
- Restriction: do not read, clone, or analyse the educational generator.

## Request to the assistant

**Role:** Data-architecture reviewer.
**Question:** Does the proposal preserve raw/temporary/curated separation,
traceability, and idempotency without fixing unobserved data as fact?
**Expected output:** Risks, decisions that require an ADR, and persistence tests.
**Evaluation criteria:** `docs/ai/evaluation-rubric.md` and Gaby's review.

## Human review of the outcome

- [ ] Facts and assumptions are separated.
- [ ] Referenced paths and documents exist.
- [ ] No Kafka fields, topics, or behaviours are invented.
- [ ] The proposal respects scope and security.
- [ ] The outcome is accepted or rejected with a reason.

## AI-use record

- Tool / role: Claude Code, data-architecture reviewer/designer
  (serving-engineer).
- Date: 2026-08-29.
- Summarised output: documentary proposal for MongoDB collections and PostgreSQL
  tables in `docs/specs/HRP-25-modelo-datos.md`; update to
  `docs/03-data-model.md`; and a `Proposed` ADR
  (`docs/adr/0006-person-correlation-key.md`) for the person correlation key,
  without fixing fields, types, or rules that are not evidenced by HRP-24/HRP-29.
- Human decision: pending.
- Reviewer: Gaby (review pending).
