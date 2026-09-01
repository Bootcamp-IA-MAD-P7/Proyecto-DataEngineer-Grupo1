# HRP-44 - Domain classification of event fragments

**Status:** Draft - pending human review  
**Owner:** Gabriela  
**Jira:** HRP-44  
**Dependencies:** HRP-34 raw persistence boundary; approved observed data contract  
**Related ADR:** `docs/adr/0006-person-correlation-key.md` (Proposed / blocked)

## Objective

Define deterministic structural classification of an event payload into Personal,
Location, Professional, Bank or Net data for downstream ETL processing.

## Context and scope

Classification uses only the payload's top-level field-name set. Values, field order
and technical Kafka metadata are not classification inputs.

| Domain | Required exact key set |
|---|---|
| Personal | `name`, `last_name`, `sex`, `telfnumber`, `passport`, `email` |
| Location | `fullname`, `city`, `address` |
| Professional | `fullname`, `company`, `company address`, `company_telfnumber`, `company_email`, `job` |
| Bank | `passport`, `IBAN`, `salary` |
| Net | `address`, `IPv4` |

An exact key-set match is required. Missing keys, extra keys, partial overlaps and
unsupported shapes produce an explicit `unknown`/`unsupported` result. The classifier
must not select the closest domain or silently apply a priority rule. The five current
key sets are pairwise distinct; any future multiple-match contract must expose
ambiguity explicitly.

### Includes

- A pure, deterministic classifier for the five exact domain shapes.
- Explicit handling of unsupported or unknown key sets.
- Tests proving order independence, value independence and non-mutation.

### Excludes

- Person correlation, `person_id` or any global identity key.
- Fragment aggregation, completeness rules or conflict resolution.
- PostgreSQL business-key upserts.
- Value normalization, cleaning or semantic validation, including email, phone,
  passport, IBAN and IP validation (HRP-45 or later scope).
- Kafka ingestion changes or mutation of MongoDB RAW documents and technical metadata.

## Design

The classifier belongs to the transformation boundary and receives a payload fragment
without changing it. Its result is one of `Personal`, `Location`, `Professional`,
`Bank`, `Net`, or `unknown`/`unsupported`, following the smallest API consistent with
the existing transformation package conventions. It never correlates payloads.

## Acceptance criteria

- [ ] **AC-01:** An exact Personal key set is classified as Personal.
- [ ] **AC-02:** An exact Location key set is classified as Location.
- [ ] **AC-03:** An exact Professional key set is classified as Professional.
- [ ] **AC-04:** An exact Bank key set is classified as Bank.
- [ ] **AC-05:** An exact Net key set is classified as Net.
- [ ] **AC-06:** Classification is independent of field ordering and field values.
- [ ] **AC-07:** Missing, extra, partial or unsupported key sets return the documented
  unknown/unsupported result and are never mapped to the closest domain.
- [ ] **AC-08:** Classification does not mutate its input or RAW/technical metadata
  and performs no person correlation or HRP-45 cleaning.
- [ ] **AC-09:** The specification and focused test strategy are documented.

## Accessibility and sustainability applicability

- Accessibility: not applicable - this is a backend transformation rule with no
  user-facing flow.
- Sustainability: applicable - the classifier is a bounded pure operation with no
  new dependency, storage, network transfer or polling; focused tests provide the
  implementation evidence.
- Deferred claims: no accessibility, carbon, energy or deployment claim is made.

## Test strategy

| Level | Case | Evidence expected |
|---|---|---|
| Unitario | AC-01 to AC-05 exact domain shapes | Each result is classified correctly |
| Unitario | AC-06 repeated classification, reordered keys and changed values | Same result; no value/order dependence |
| Unitario | AC-07 missing, extra, partial and unsupported shapes | Explicit unknown/unsupported result |
| Unitario | AC-08 input and metadata non-mutation | Inputs remain unchanged; no identity logic |

Tests will be placed under `tests/unit/`, named by behavior, and use synthetic
fixtures without live payloads, as required by `docs/05-test-harness.md`.

## Evidence of closure

- Branch / PR: pending human review
- Commit: not created
- Commands and result: documentation validation pending
- Jira closure comment: not applicable before review and merge
