# ADR-0006: Person correlation key for curated storage

## Status

Proposed — blocked pending evidence. Not accepted; do not treat as an invariant.

## Context

The curated PostgreSQL model needs a way to associate raw structural variants
(A–E, per `docs/02-data-contract.md`) that plausibly belong to the same person, so
that `employees`, `locations`, `professional_profiles`, `bank_accounts` and
`network_data` can be joined without duplicating a person across tables.

HRP-29's bounded observation identifies `passport`, `fullname` and `address` as
correlation *candidates* only, because their raw names occur in more than one
variant. It explicitly did not compare their values or establish equality,
uniqueness, normalisation, priority or business meaning
(`docs/observations/2026-08-27-HRP-29-kafka.md`). `docs/specs/HRP-25-modelo-datos.md`
therefore proposes a curated schema with no unique or foreign-key constraint that
would encode a correlation rule.

## Decision this ADR must eventually record

This ADR is a placeholder for a decision not yet made. It will need to state, once
evidence exists:

1. Which observed field (or combination) is the person correlation key.
2. How values are normalised before comparison (if at all).
3. How conflicts are resolved when two raw events plausibly matching the same key
   disagree on other field values.
4. What constitutes a "complete" person record versus a partial one still awaiting
   more raw events.
5. Whether the key is enforced as a database uniqueness constraint or resolved
   procedurally by `process-worker` before an upsert.

None of these five points are decided by this ADR. No default is assumed in the
interim; `docs/specs/HRP-25-modelo-datos.md` designs curated tables without a unique
business constraint until this ADR is accepted.

## Required evidence before acceptance

- Kafka observation (beyond HRP-29's bounded sample) that compares actual values of
  `passport`, `fullname` and/or `address` across variants for the same underlying
  person, obtained through an authorised, in-scope observation task (not by reading
  the educational generator).
- A documented decision, reviewed by a human, on uniqueness and conflict resolution
  for the chosen key.
- Test evidence that the chosen key does not silently merge two different people or
  split one person into two curated records.

## Consequences of staying `Proposed`

- `employees`, `locations`, `professional_profiles`, `bank_accounts` and
  `network_data` remain linkable only through the foreign keys described in
  `docs/specs/HRP-25-modelo-datos.md`, with cardinality also left `pending`.
- No curated upsert can be implemented with a business-key `ON CONFLICT` clause
  until this ADR is accepted.
- HRP-25 is not blocked by this ADR remaining `Proposed`: it documents the boundary
  without assuming an answer.

## Acceptance gate

The status may change from `Proposed` to `Accepted` only after the evidence above is
gathered under its own Jira task, reviewed by a human, and the five decision points
above are filled in with the approved answer and its evidence reference.
