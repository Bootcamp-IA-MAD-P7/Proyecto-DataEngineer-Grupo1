# HRP-61 - Group Personal Data by person

**Status:** Implementation complete; pending human review
**Owner:** Gabriela Granja
**Jira:** HRP-61
**Branch:** `feature/HRP-61-group-personal-by-person`
**Dependencies:** HRP-43 correlation evidence; HRP-44 domain classification; HRP-45 validation boundary
**Sibling precedents:** HRP-46 Location grouping; HRP-47 Professional grouping; HRP-48 Bank grouping; HRP-49 Net grouping
**Related ADR:** `docs/adr/0006-person-correlation-key.md` (Proposed / blocked for global identity)

## Objective

Define a pure, deterministic Personal-domain transformation that groups fragments
by the exact delivered `passport` value as a Personal-domain operational bucket
key. This is a domain-local processing decision only. It does not establish
global identity, passport uniqueness, a real-world person identifier or a
synthetic `person_id`.

## Authorized evidence and classification

- HRP-44 defines the exact Personal structural key set as
  `{"name", "last_name", "sex", "telfnumber", "passport", "email"}`.
- HRP-45 defines the upstream structural validation boundary and performs no
  semantic validation or identity resolution.
- HRP-43 documents `passport` as a partial Personal/Bank correlation candidate;
  it does not prove uniqueness, identity, universal coverage or semantics.
- ADR-0006 remains Proposed and blocked for global identity.
- HRP-46 through HRP-49 establish the sibling pattern of exact, domain-local
  operational grouping without cross-domain identity.

The Personal shape is **CONTRACTUAL** evidence from HRP-44. The Personal/Bank
`passport` relationship is **OBSERVED** evidence from HRP-43. Exact `passport`
as a Personal-only operational bucket key is the **ARCHITECTURAL DECISION** of
this specification. It is independent of HRP-48's Bank-only operational key and
does not authorize Personal/Bank consolidation.

No generator source, generator log, live/raw payload or generator-derived
fixture is used or required by this specification.

## Dependencies and boundaries

HRP-44 classification and HRP-45 validation are upstream contractual
dependencies. HRP-43 is evidence for the candidate relationship, not a global
identity decision. HRP-46 through HRP-49 are sibling implementation precedents,
not runtime coupling.

Persistence, Kafka, MongoDB RAW, Redis, PostgreSQL, API, frontend and
infrastructure are outside this specification. No global identity decision is
required for this domain-local operation, but human review is required before
implementation.

## Scope

### Included

- A typed pure Personal-domain grouper.
- Exact raw `passport` operational bucket grouping within Personal only.
- Explicit grouped, ambiguous, uncorrelated and unsupported outcomes.
- Exact repeated-evidence deduplication within a domain-local bucket.
- Deterministic ordering independent of input arrival order.
- Synthetic unit-test cases for every runtime acceptance criterion.

### Excluded

- Global `person_id`, real-world identity or business uniqueness.
- Personal/Bank correlation merely because both domains expose `passport`.
- Cross-domain joins or transitive identity inference.
- Normalization, trimming, case folding, canonicalization or fuzzy matching.
- Fallback keys using `name`, `last_name`, `email`, `telfnumber` or any other
  field.
- Semantic validation of passport, name, email, telephone, sex or any other
  Personal value.
- Conflict precedence, latest-value-wins or first-value-wins behavior.
- Final consolidated person records or HRP-50 implementation.
- PostgreSQL business-key constraints, upserts or persistence changes.
- Changes to HRP-43, HRP-44, HRP-45, HRP-46, HRP-47, HRP-48, HRP-49 or
  ADR-0006.

## Personal structural contract

The supported Personal payload has exactly these top-level keys:

```text
{"name", "last_name", "sex", "telfnumber", "passport", "email"}
```

Classification and validation remain upstream contracts. This grouper must not
reclassify input, duplicate their field definitions, apply semantic cleaning or
interpret the values.

## Operational grouping contract

`passport` is the exact Personal-domain operational bucket key. Equality is
exact string equality. The operation performs no trimming, case conversion,
case folding, punctuation change, canonicalization, normalization, fuzzy
matching or heuristic matching.

Equal usable `passport` strings share one Personal operational bucket. Different
usable strings remain in separate buckets. Equal values do not necessarily
represent the same real-world person and do not authorize correlation with the
Bank domain.

No fallback to `name`, `last_name`, `email`, `telfnumber`, a composite key,
Kafka coordinates or another field is allowed.

## Input and output contracts

Input is an iterable of `ClassifiedFragment` values containing JSON-compatible
payload evidence and its supplied classification context. A valid Personal
fragment must pass the upstream validation boundary and have classification
`Personal`. Inputs must not be mutated.

The proposed public transformation API is:

```text
group_personal_fragments(
    fragments: Iterable[ClassifiedFragment],
) -> PersonalGroupingResult
```

`PersonalGroupingResult` contains deterministic `PersonalGroup` values and
unresolved entries. Each group contains:

- `key`: the exact usable `passport` string;
- `status`: `grouped` or `ambiguous`; and
- `fragments`: distinct Personal payload evidence preserved in the group.

Unresolved entries preserve the payload, classification context and a technical
reason. No persistence target, global identifier or PostgreSQL key is present.

## Result states and edge behavior

- **grouped:** one distinct Personal payload exists in a usable-passport bucket.
- **ambiguous:** multiple distinct Personal payloads share the exact usable
  passport; all evidence is preserved without precedence or merge resolution.
- **uncorrelated:** an accepted Personal payload has a present but unusable
  `passport`, such as an empty string, null or non-string value.
- **unsupported:** the input is malformed, non-Personal, unknown, incomplete,
  extra-key, structurally missing `passport`, or inconsistent with the upstream
  classification/validation boundary.

Structurally missing `passport` is unsupported because it does not satisfy the
exact Personal shape. A present empty, null or non-string value is uncorrelated;
no key is fabricated and no fallback is attempted.

Exact repeated JSON-compatible payload evidence is represented once within a
bucket. This is transformation-level evidence deduplication only. It is not
Kafka event idempotency, business duplicate resolution, global identity or
PostgreSQL upsert behavior.

Groups, fragments and unresolved outcomes are ordered deterministically using a
canonical JSON representation. Equivalent inputs in different arrival orders
produce the same semantic result. Distinct same-passport evidence remains
explicit and is not silently discarded.

## Identity and persistence boundaries

`passport == Personal-domain operational bucket key` only. It is not:

- a global person identifier;
- a proven unique business key;
- a synthetic `person_id`;
- authorization for Personal/Bank consolidation; or
- a final-record identity for HRP-50.

Kafka `topic + partition + offset` remains technical event provenance and raw
idempotency evidence only. HRP-61 does not modify Kafka, MongoDB RAW, Redis,
PostgreSQL, APIs, frontend or infrastructure.

ADR-0006 remains unchanged and Proposed. Any future cross-domain aggregation,
business uniqueness or curated business-key upsert requires the separately
approved ADR-0006 decision and its final-record specification.

## Acceptance criteria

- [ ] **AC-01:** A structurally valid Personal fragment accepted by the upstream
      boundaries is retained without semantic mutation.
- [ ] **AC-02:** Personal fragments with equal exact usable `passport` strings
      share one Personal-domain operational bucket.
- [ ] **AC-03:** Personal fragments with different exact usable `passport`
      strings remain in separate buckets, without normalization.
- [ ] **AC-04:** Reordering equivalent input does not change groups, preserved
      evidence or unresolved outcomes.
- [ ] **AC-05:** Exact repeated equivalent payload evidence is represented once
      within its bucket and does not create nondeterministic output.
- [ ] **AC-06:** Structurally missing `passport` is unsupported; a present empty,
      null or non-string `passport` is uncorrelated; no fallback is used.
- [ ] **AC-07:** Distinct Personal payloads sharing an exact `passport` are all
      preserved and the bucket is marked ambiguous without silent conflict
      resolution.
- [ ] **AC-08:** Malformed, unknown, non-Personal, incomplete, extra-key or
      classification-inconsistent input produces an explicit unsupported result.
- [ ] **AC-09:** Payloads, classification context and upstream evidence remain
      unchanged by grouping.
- [ ] **AC-10:** No normalization, fallback, global identity, Personal/Bank
      consolidation, cross-domain join, final record or persistence behavior is
      introduced.

## Test strategy

Focused unit tests must use synthetic JSON-compatible fixtures only. They must
not use generator-derived data or assert global identity.

| Acceptance criterion | Test evidence |
|---|---|
| AC-01 | `test_valid_personal_payload_is_retained_ac01` |
| AC-02, AC-03 | `test_same_and_different_passports_define_personal_groups_ac02_ac03` |
| AC-04, AC-05 | `test_duplicate_personal_payloads_are_deterministic_ac04_ac05` |
| AC-06 | `test_missing_personal_passport_is_unsupported_ac06`; `test_unusable_personal_passport_is_uncorrelated_ac06` |
| AC-07 | `test_distinct_same_passport_personal_evidence_is_ambiguous_ac07` |
| AC-08 | `test_unsupported_personal_input_is_explicit_ac08` |
| AC-09, AC-10 | `test_personal_grouping_preserves_boundaries_ac09_ac10` |

Tests must not assert that equal passports identify the same real person, that
Personal and Bank records belong together, or that a passport is globally
unique.

## Definition of Ready

The Personal structural contract, upstream classification and validation
boundaries, exact local grouping semantics, acceptance criteria and focused
synthetic test strategy are defined. The implementation does not require
generator access or resolution of global identity. Human review remains required
before merge and closure.

## Definition of Done

- The specification, smallest Personal-domain implementation and focused
  synthetic tests are available for human review and match this contract.
- Specification commit: `01b01e5` (`docs(HRP-61): specify Personal grouping by person`).
- Implementation commit: `30e2d00` (`feat(HRP-61): group Personal fragments by person`).
- Focused behavior, type, lint and specification validation evidence is recorded
  in this document; repository-wide limitations are recorded separately here.
- Human review, commit, push, PR creation, PR merge and Jira closure remain
  pending and are not claimed.

## Risks and limitations

Equal passport values may belong to different people, and different passport
values may belong to the same person. The local bucket key therefore cannot be
used for global identity or Personal/Bank consolidation.

Personal values may be missing, malformed or semantically invalid because
semantic validation is outside this task. Distinct same-passport evidence is
preserved as ambiguous rather than resolved.

A future ADR-0006 decision may change global aggregation, curated persistence or
the final HRP-50 record. HRP-61 must not anticipate that decision.

## Accessibility and sustainability applicability

- Accessibility: not applicable - this is a backend transformation specification
  with no user-facing flow.
- Sustainability: applicable through a pure, bounded, deterministic operation
  with no new dependency, persistence, network transfer or polling. No measured
  efficiency claim is made.
- Deferred claims: no accessibility conformance, carbon, energy or deployment
  claim is made.

## Traceability

```text
Jira HRP-61
  -> this specification
  -> HRP-43 correlation evidence
  -> HRP-44 Personal structural classification
  -> HRP-45 validation boundary
  -> exact Personal `passport` operational grouping
  -> HRP-46/47/48/49 domain-local grouping precedents
  -> ADR-0006 global identity limitation
  -> commit `01b01e5` specification
  -> commit `30e2d00` implementation
```

## Evidence and status

- Specification: completed; pending human review.
- Production implementation: `src/hr_pro_platform/transformation/personal_grouper.py`.
- Specification commit: `01b01e5` (`docs(HRP-61): specify Personal grouping by person`).
- Implementation commit: `30e2d00` (`feat(HRP-61): group Personal fragments by person`).
- Focused tests: `tests/unit/test_personal_grouper.py`; 11 tests passed with
  repository coverage options disabled. The standard focused command also
  passed all 11 assertions but exited on the repository-wide 75% coverage gate.
- Full pytest: 124 passed, 3 skipped and 3 environment-related errors caused by
  Windows temporary-directory permission failures in existing tests.
- Ruff check: repository-wide command passed with permission warnings for
  inaccessible pre-existing paths; changed files passed targeted Ruff checks.
- Ruff format: changed files passed targeted format checking. The repository-wide
  command is blocked by pre-existing unformatted files under
  `.pre-commit-home-hrp44-final` and `.tmp-pre-commit-hrp46`.
- Mypy: `mypy src` passed for 22 source files.
- Specification validation: `scripts/validate_specs.py` passed for 27 specification files.
- `git diff --check`: passed.
- Commit, push, PR, merge and Jira closure: not performed or claimed.

## ADR impact

No change to ADR-0006 is required or authorized. HRP-61 defines only a
Personal-domain operational grouping decision. It does not authorize global
identity, Personal/Bank consolidation, business uniqueness or HRP-50 final
record construction.
