# HRP-49 - Group Net Data by person

**Status:** Implementation-ready; pending human review
**Owner:** Gabriela Granja
**Jira:** HRP-49
**Branch:** `feature/HRP-49-group-net-by-person`
**Dependencies:** HRP-44 classification; HRP-45 validation
**Sibling precedents:** HRP-47 Professional grouping; HRP-48 Bank grouping
**Related ADR:** `docs/adr/0006-person-correlation-key.md` (Proposed / unresolved)

## Objective

Define a pure, deterministic Net-domain transformation that groups fragments by
the exact delivered `address` value as a Net-domain operational grouping key.
This does not establish global identity, uniqueness, a real-world identity key,
a synthetic `person_id`, or cross-domain aggregation authorization.

## Authoritative evidence and boundaries

- HRP-44 defines the exact Net key set as `{"address", "IPv4"}`.
- HRP-45 defines structural validation as agreement between the supplied
  classification and `classify_payload(payload)`; it performs no semantic cleaning.
- HRP-43 documents `address` only as a partial Location/Net correlation candidate.
- ADR-0006 remains unchanged and unresolved for global identity.
- HRP-47 and HRP-48 are sibling implementation precedents, not runtime dependencies.

No generator source, generator logs, live data or raw payloads are used.

## Scope

Included are the typed pure grouper, explicit result states, exact address
grouping, duplicate evidence deduplication, deterministic ordering and synthetic
unit tests. Excluded are identity, cross-domain aggregation, normalization,
semantic validation, IPv4 fallback or composite keys, persistence, infrastructure,
and refactoring of sibling groupers.

## Design

The grouper consumes `ClassifiedFragment` values and reuses `validate_fragment`.
It accepts only payloads with the exact Net key set and classification `Net`.
The exact non-empty string `address` is the only operational key. IPv4 is retained
as payload evidence but is not interpreted.

Valid evidence is placed in an exact-address bucket. Exact duplicate payloads are
represented once. A bucket with one distinct payload is `grouped`; a bucket with
multiple distinct payloads is `ambiguous`. Present empty, null or non-string
addresses are `uncorrelated`. Missing address and all validation failures are
`unsupported`.

Groups, payloads and unresolved outcomes are sorted using canonical JSON with
sorted keys and compact separators. Inputs and classification context are not
mutated.

## Input and output contracts

Input is an iterable of JSON-compatible `ClassifiedFragment` values. A valid Net
fragment must pass the existing validator and have classification `Net`. The
output is `NetGroupingResult(groups, unresolved)`, with `NetGroup.fragments` typed
as `tuple[JSONPayload, ...]`. No persistence target or person identifier is present.

## Invariants and exclusions

- `address` is a Net-domain operational key only.
- It is not global identity, a proven unique business key or `person_id`.
- No trimming, case folding, normalization, fuzzy matching or heuristics occur.
- IPv4 is never a fallback, composite key or conflict resolver.
- Distinct same-address evidence is preserved without precedence or merging.
- No Kafka, MongoDB, Redis, PostgreSQL, API, frontend or infrastructure behavior changes.

## Acceptance criteria

- [ ] **AC-01:** A structurally valid Net payload accepted by the existing validation boundary is retained without semantic mutation.
- [ ] **AC-02:** Equal exact usable addresses share one Net-domain bucket; different exact addresses remain separate.
- [ ] **AC-03:** Exact duplicate payload evidence is represented once and output is input-order independent.
- [ ] **AC-04:** Missing address is unsupported; present empty, null or non-string address is uncorrelated.
- [ ] **AC-05:** Distinct payloads sharing an exact address are all preserved and the bucket is ambiguous.
- [ ] **AC-06:** Malformed, unknown, non-Net, incomplete, extra-key or classification-inconsistent input is unsupported.
- [ ] **AC-07:** Payloads and classification context remain unchanged.
- [ ] **AC-08:** No normalization, fallback, identity, cross-domain, semantic validation, persistence or infrastructure scope is introduced.

## Test strategy

Focused unit tests use synthetic JSON-compatible fixtures only:

| Acceptance criterion | Test |
|---|---|
| AC-01 | `test_valid_net_payload_is_retained_ac01` |
| AC-02 | `test_same_and_different_addresses_define_domain_local_groups_ac02` |
| AC-03 | `test_duplicate_net_payloads_are_deterministic_ac03` |
| AC-04 | `test_missing_net_address_is_unsupported_ac04`; `test_unusable_net_address_is_uncorrelated_ac04` |
| AC-05 | `test_distinct_same_address_evidence_is_ambiguous_ac05` |
| AC-06 | `test_unsupported_net_input_is_explicit_ac06` |
| AC-07 | `test_net_grouping_preserves_payload_and_context_ac07` |
| AC-08 | `test_net_grouping_has_no_normalization_fallback_or_identity_ac08` |

## Definition of Ready

HRP-44 and HRP-45 are available, the Net contract is unchanged, and the task is
implemented on `feature/HRP-49-group-net-by-person` from the merged HRP-48 base.

## Definition of Done

The specification, smallest Net sibling implementation and focused synthetic
tests exist. The implementation commit is recorded in Git, the branch is pushed,
and Pull Request [#40](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/40)
has been created. Human approval, merge and Jira closure remain pending.

## Evidence and status

- Implementation commit: `f759f0e8b4f23cc8d02a644049c6b377c2b5a95`
  (`HRP-49 feat: group Net fragments by person`).
- Branch: `feature/HRP-49-group-net-by-person`, present on `origin`.
- Pull Request: [#40](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/40).
- GitHub CI/check status: PR governance green; PR labels green; quality green.
- Local specification validation for this review fix: passed (`26` specifications).
- Human approval: pending.
- Merge: pending.
- Jira closure: pending.

## Risks and limitations

Equal addresses may belong to different people, and different addresses may belong
to the same person. Address and IPv4 values may be semantically invalid because
semantic validation is not authorized. ADR-0006 may change future global design;
HRP-49 must not anticipate that decision.

## Accessibility and sustainability applicability

- Accessibility: not applicable; this is a backend transformation with no user-facing flow.
- Sustainability: applicable through a pure, bounded, deterministic operation with no new dependency, storage or network transfer.
- Deferred claims: no accessibility conformance, carbon, energy or deployment claim is made.

## ADR impact

No change to ADR-0006 is required or authorized.
