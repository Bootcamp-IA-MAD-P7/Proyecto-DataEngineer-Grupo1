# HRP-48 - Group Bank Data by person

**Status:** Implementation-ready; pending human review  
**Owner:** Gabriela Granja  
**Jira:** HRP-48  
**Branch:** `feature/HRP-48-group-bank-by-person`  
**Base:** `2ead5fb` (`HRP-47 feat: group Professional fragments by person (#38)`)  
**Dependencies:** HRP-44 classification; HRP-45 validation; HRP-43 correlation evidence  
**Sibling precedent:** HRP-47 is an implementation precedent, not a runtime dependency.  
**Related ADR:** `docs/adr/0006-person-correlation-key.md` (Proposed / blocked for global identity)

## Objective

Define a pure, deterministic Bank-domain transformation that groups fragments by
the exact delivered `passport` value as a Bank-domain operational bucket key.
This does not establish global identity, passport uniqueness, a real-world
identity key or a synthetic `person_id`.

## Authorized evidence and classification

- HRP-44 defines the exact Bank structural key set as `{"passport", "IBAN", "salary"}`.
- HRP-45 accepts a supplied classification only when it agrees with the exact
  HRP-44 structural classification and performs no semantic cleaning.
- HRP-43 documents `passport` only as a partial Personal/Bank correlation
  candidate; it does not prove uniqueness, identity, coverage or semantics.
- ADR-0006 remains Proposed / blocked for global identity.

The key set is **CONTRACTUAL** evidence from HRP-44. The partial passport
relationship is **OBSERVED** evidence from HRP-43. Exact `passport` as a
Bank-only operational bucket key is this task's **ARCHITECTURAL DECISION**.
No generator source, generator log or live/raw data is used.

## Dependencies and boundaries

HRP-44 classification and HRP-45 validation are actual upstream contractual
dependencies. HRP-47 is a sibling implementation precedent only; there is no
runtime coupling. Persistence, Kafka, MongoDB RAW, Redis, PostgreSQL, API and
infrastructure are not dependencies or implementation targets.

Included scope is the typed pure grouper, explicit outcomes, deterministic
ordering, exact-payload evidence deduplication and synthetic unit tests.
Excluded scope is global or synthetic identity, cross-domain aggregation,
business deduplication, semantic validation, normalization, fallback keys,
persistence and infrastructure changes.

## Bank structural contract

The supported Bank payload has exactly the top-level keys `passport`, `IBAN` and
`salary`. Classification and validation remain upstream contracts; this grouper
does not duplicate their definitions, reclassify input or add semantic checks.

## Operational grouping contract

`passport` is an exact Bank-domain operational bucket key. Equality is exact
string equality: no trimming, case conversion, case folding, punctuation change,
canonicalization or other normalization is allowed. No fallback to `IBAN` or
`salary`, composite key, fuzzy match or heuristic is allowed. Equal values share
one Bank bucket; different values remain separate. Equal values do not
necessarily represent the same real person.

## Input and output contracts

Input is an iterable of `ClassifiedFragment` values containing JSON-compatible
payload evidence and its supplied classification context. A valid Bank fragment
must pass `validate_fragment` and have classification `Bank`. The function does
not mutate payloads, context, upstream results, RAW records or technical
metadata.

Output is `BankGroupingResult(groups, unresolved)`. Each `BankGroup` contains
the exact string key, a status, and distinct payload evidence as
`tuple[JSONPayload, ...]`. Each unresolved result preserves payload and
classification context and gives a status and technical reason. No persistence
target or person identifier is present.

## Result states and edge behavior

- **grouped:** one distinct Bank payload in a usable-passport bucket.
- **ambiguous:** multiple distinct Bank payloads share the exact usable passport;
  all evidence is preserved, with no precedence or merge rule.
- **uncorrelated:** an accepted Bank payload has a present but unusable passport,
  such as an empty string, null or non-string value.
- **unsupported:** malformed, unknown, non-Bank, incomplete, extra-key,
  structurally missing-passport or classification-inconsistent input fails the
  upstream boundary. It is not repaired, coerced or reinterpreted.

Exact repeated JSON-compatible payload evidence is represented once within a
bucket. This is transformation-level deduplication only, not event identity,
global business deduplication or PostgreSQL upsert behavior. Groups, evidence
and unresolved outcomes are ordered deterministically using canonical JSON
serialization; results do not depend on input order. Input mappings and
classification context remain unchanged.

## Identity and persistence boundaries

`passport == Bank-domain operational bucket key` only. It is not global person
identity, a proven unique business key, a synthetic `person_id`, or authorization
for Personal/Bank consolidation. ADR-0006 is unchanged. HRP-48 does not modify
Kafka, MongoDB RAW, Redis, PostgreSQL, APIs, frontend or infrastructure.

## Acceptance criteria

- [ ] **AC-01:** Valid Bank payloads pass the existing structural boundary and are retained unchanged, without semantic validation.
- [ ] **AC-02:** Exact equal passport strings group together and different strings remain separate, with no normalization.
- [ ] **AC-03:** Exact duplicate payload evidence appears once and equivalent reordered input produces the same result deterministically.
- [ ] **AC-04:** Missing passport is unsupported; present empty, null or non-string passport is uncorrelated; no fallback is used.
- [ ] **AC-05:** Distinct same-passport payloads are all preserved and the group is ambiguous; no silent conflict resolution occurs.
- [ ] **AC-06:** Unknown, malformed, non-Bank, incomplete, extra-key or inconsistent input is explicitly unsupported.
- [ ] **AC-07:** Payloads and context are immutable, and upstream, storage and infrastructure behavior is unchanged.
- [ ] **AC-08:** No normalization, fallback, identity, cross-domain or persistence scope is introduced.

## Test strategy

Focused unit tests use synthetic JSON-compatible fixtures only:

| Acceptance criteria | Test evidence |
|---|---|
| AC-01 | `test_valid_bank_payload_is_retained_ac01` |
| AC-02 | `test_same_and_different_passports_define_domain_local_groups_ac02` |
| AC-03 | `test_duplicate_bank_payloads_are_deterministic_ac03` |
| AC-04 | `test_missing_bank_passport_is_unsupported_ac04`; `test_unusable_bank_passport_is_uncorrelated_ac04` |
| AC-05 | `test_distinct_same_passport_evidence_is_ambiguous_ac05` |
| AC-06 | `test_unsupported_bank_input_is_explicit_ac06` |
| AC-07 | `test_bank_grouping_preserves_payload_and_context_ac07` |
| AC-08 | `test_bank_grouping_has_no_normalization_fallback_or_identity_ac08` |

Tests do not assert global uniqueness, real-person identity, cross-domain
correlation, persistence or unapproved semantic rules.

## Definition of Ready

The Bank structural contract, upstream classification and validation boundaries,
operational key semantics, acceptance criteria and focused test strategy are
defined. The task does not require generator access or an unresolved global
identity decision. Human review remains a governance gate.

## Definition of Done

The spec, smallest Bank sibling implementation and focused tests exist; relevant
specification, lint, format, type and test checks pass; and the change is ready
for human review. Commit, push, PR merge, Jira mutation and closure remain human
actions and are not claimed here.

## Risks and limitations

Equal passport values may belong to different people, and different values may
belong to the same person. Passport, IBAN and salary values may be semantically
invalid because semantic validation is not authorized. Future ADR-0006 decisions
may alter global aggregation or persistence design; this task must not anticipate
those decisions.

## Accessibility and sustainability applicability

Accessibility is not applicable: this is a backend transformation with no
user-facing flow. Sustainability applies through a pure, bounded, deterministic
operation with no new dependency, storage, network transfer or polling. No
formal accessibility, carbon, energy or deployment claim is made.

## Evidence and status

The HRP-48 implementation and focused tests exist in this branch. The
implementation commit is `430308c`, and PR #39 exists with green GitHub
checks. Local focused HRP-48 tests passed, as did the relevant HRP-47 + HRP-48
regression tests. The local repository-wide pytest run reported `104 passed, 3
skipped, 3 errors`; the three errors were environment/temp-directory permission
errors, not HRP-48 assertion failures. This local limitation is preserved
separately from the successful GitHub PR checks, which are the merge/PR
validation evidence. Human approval and merge remain pending. Jira closure is
not claimed.

## ADR impact

No change to ADR-0006 is required or authorized. HRP-48 is strictly a
Bank-domain operational grouping decision.
