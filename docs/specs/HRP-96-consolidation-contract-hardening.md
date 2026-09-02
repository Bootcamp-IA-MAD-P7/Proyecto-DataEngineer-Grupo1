# HRP-96 - Person consolidation contract hardening

**Status:** Implementation ready; pending human review
**Owner:** Gabriela Granja
**Jira:** HRP-96
**Dependencies:** HRP-50 and ADR-0006
**Related ADR:** `docs/adr/0006-person-correlation-key.md`

## Objective

Remove post-merge inconsistencies from the HRP-50 transformation contract before
PostgreSQL integration depends on `ConsolidatedPersonRecord`.

## Context and scope

Included:

- one shared, typed `UnresolvedFragment` contract for every domain grouper;
- explicit retention of original same-domain group boundaries in a consolidated
  component;
- a focused ambiguity test for multiple same-domain groups connected transitively;
- accurate HRP-50 status and traceability.

Excluded:

- changes to the four exact correlation edges accepted by ADR-0006;
- normalization, fuzzy matching, fallback identity or new business rules;
- Kafka, MongoDB, PostgreSQL, Docker, API, frontend or persistence behavior;
- real payloads, PII or educational generator access.

Assumptions and risks:

- source references remain opaque, upstream-supplied identifiers;
- retaining group boundaries extends the transformation output contract and must be
  reviewed before downstream persistence work relies on it;
- compatibility access to flattened fragments remains available, but consumers that
  need ambiguity evidence must use the explicit groups.

## Design

`fragment_contract.py` owns the common unresolved-fragment representation. Every
grouper emits it with status, payload, classification, source reference and reason.
The consolidator consumes the typed result unions directly.

`DomainContribution` retains an ordered tuple of `DomainGroupContribution` values.
Each value records the original domain-local key and fragments. A read-only
`fragments` compatibility view exposes the flattened evidence while the canonical
contract preserves group boundaries.

## Acceptance criteria

- [x] Every grouper uses the shared unresolved-fragment contract.
- [x] The consolidator requires no `getattr` or `type: ignore` for heterogeneous
  grouper contracts.
- [x] Multiple groups from one domain in a connected component produce an ambiguous
  record without losing fragments, group keys or source provenance.
- [x] Reordered input produces the same result and caller-owned inputs are unchanged.
- [x] HRP-50 status, output contract and merge evidence are current.
- [x] ADR-0006 correlation edges and out-of-scope systems are unchanged.

## Accessibility and sustainability applicability

- Accessibility: not applicable; this change has no user-facing flow.
- Sustainability: applicable only through deterministic in-memory processing and no
  new services, polling, persistence or dependencies.
- Deferred claims: no accessibility-conformance, energy, carbon or deployment claim
  is made.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Unit | Shared unresolved contract | All groupers expose the same typed fields |
| Unit | Two Personal groups connected through one Location group | Ambiguous record retains both group keys, fragments and provenance |
| Unit | Reordered input and immutability | Equal output; inputs unchanged |
| Regression | Existing transformation suite | Existing behavior remains green |

## Completion evidence

- Branch / PR: `feature/HRP-96-consolidation-contract-hardening` / pending
- Commit: pending
- Commands and results:
  - affected-file `ruff check`: passed;
  - affected-file `ruff format --check`: passed;
  - `mypy src`: passed for 24 source files;
  - targeted transformation tests: 59 behavior tests passed; the isolated command
    correctly did not satisfy the repository-wide coverage gate;
  - `pytest`: 138 passed, 5 environment-dependent integration tests skipped, 88.58%
    coverage (75% required);
  - `python scripts/validate_specs.py`: 29 specifications passed;
  - `git diff --check`: passed.
- Jira closure comment: pending human review and merge
