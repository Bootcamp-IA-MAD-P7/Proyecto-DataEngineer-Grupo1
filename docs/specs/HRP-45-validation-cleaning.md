# HRP-45 - Validation and cleaning boundary

**Status:** Implemented - PR #36; pending final approval or merge
**Owner:** Gabriela
**Jira:** HRP-45
**Dependencies:** HRP-34 raw persistence boundary; HRP-44 domain-classification contract
**Related ADR:** None. ADR-0006 remains Proposed and blocked and is explicitly outside this task.

## Objective

Define the smallest deterministic transformation-stage validation boundary for a
classified event fragment without inventing unsupported business rules or
changing the MongoDB RAW boundary.

## Context and scope

The component runs downstream of RAW persistence and consumes a fragment together
with the result of the HRP-44 structural classifier. Payload/classification
structural consistency is validated by reusing the HRP-44 `classify_payload`
contract. A supported classification is valid only when
`classify_payload(payload) == classification`. This is structural contract
validation only; it does not imply semantic field-value validation. The current
data contract
does not define field formats, ranges, requiredness, nullability, semantics or
normalization for observed business values.

### Includes

- A pure, testable validation result for a classified fragment.
- Explicit handling of malformed input and unsupported classification.
- Deterministic behavior and input non-mutation.
- Documentation of unresolved business validation and cleaning decisions.

### Excludes

- Mutation, replacement or deletion of MongoDB RAW documents.
- Changes to Kafka ingestion, acknowledgement or technical-invalid routing.
- Semantic validation of email, phone, passport, IBAN, salary, IP, sex or
  address-like values.
- Trimming, case conversion, canonicalization, coercion, defaults or inferred
  values.
- Person correlation, identity keys, aggregation, completeness, uniqueness or
  PostgreSQL business-key upserts.

## Design

The smallest approved API is a pure function at the transformation boundary:

```text
validate_fragment(payload: object, classification: Classification) -> ValidationResult
```

`ValidationResult` contains at minimum:

- `is_valid`: explicit boolean status;
- `classification`: the supplied supported or unsupported context;
- `errors`: a deterministic, inspectable collection of technical reasons; and
- `payload`: the original object when valid, with no semantic cleaning applied.

The concrete Python types and naming must follow existing transformation-package
conventions during implementation. The function must not mutate its arguments.
No persistence or error-collection routing is specified here: the repository
defines technical `invalid_events` handling for non-processable ingestion input,
but does not define downstream routing for business-invalid transformation data.
Therefore this task returns an explicit result and leaves persistence/routing out
of scope.

## Defined behavior

- An object-like payload paired with one of the five HRP-44 supported domain
  classifications is accepted only when `classify_payload(payload)` returns the
  supplied classification; no unapproved business validation is applied.
- A supported classification that disagrees with `classify_payload(payload)`
  produces an explicit `classification_mismatch` error.
- Results are deterministic for equivalent inputs and classification context.
- Malformed or non-mapping input is rejected explicitly by the result API; it is
  not repaired or converted into a fabricated object.
- `unknown`/`unsupported` classification is represented explicitly and is never
  silently mapped to a known domain.
- The valid result preserves the input payload as-is.
- No semantic normalization is currently authorized. In particular, no trimming,
  case conversion or other canonicalization may be performed.
- Missing business values are not inferred and defaults are not introduced.
- Validation errors are explicit and testable; no error may expose sensitive
  payload content.

## Explicitly undefined decisions

The following remain unresolved and must not be guessed in HRP-45 implementation:

- email, phone, passport, IBAN and IP formats;
- salary ranges or numeric semantics;
- `sex` values or enumeration;
- address semantics or canonical form;
- required, optional and nullable field rules;
- semantic validity versus structural conformance;
- normalization, conflict handling and completeness; and
- persistence, retry, quarantine or downstream routing for transformation-invalid
  results.

Any future decision on these points requires an SDD/specification update and,
where the contract or architectural boundary changes, the applicable ADR review.

## Dependency decision

HRP-45 consumes the domain classification contract established by HRP-44. This
is a contractual dependency, not a person-correlation dependency. Implementation
must branch from updated `develop` after HRP-44 is merged, unless the team
explicitly approves a stacked-branch workflow. HRP-45 does not accept or depend
on ADR-0006.

## Acceptance criteria

- [ ] **AC-01:** A structurally supported, classified fragment is accepted without
  invented business validation when the supplied classification matches
  `classify_payload(payload)`.
- [ ] **AC-02:** Equivalent input and classification context produce the same
  validation result.
- [ ] **AC-03:** Validation does not mutate the input payload or technical metadata.
- [ ] **AC-04:** Malformed or non-mapping input produces an explicit invalid result
  without fabrication or silent coercion.
- [ ] **AC-04a:** An empty, structurally unsupported, or wrong-domain mapping
  produces `classification_mismatch` when a supported classification is supplied.
- [ ] **AC-05:** Unknown or unsupported classification is handled explicitly and
  is not mapped to a known domain.
- [ ] **AC-06:** The implementation contains no person correlation, aggregation or
  identity logic.
- [ ] **AC-07:** No unsupported semantic cleaning or normalization is performed.
- [ ] **AC-08:** Status, classification context and validation reasons are explicit
  and testable, without logging sensitive payload values.
- [ ] **AC-09:** Undefined business rules are documented as unresolved rather than
  guessed.
- [ ] **AC-10:** This specification and its focused test strategy are reviewed and
  validated before implementation.

## Accessibility and sustainability applicability

- Accessibility: not applicable - this is a backend transformation component with
  no user-facing flow.
- Sustainability: applicable - the proposed operation is pure, bounded and adds
  no dependency, persistence, polling or network transfer. Tests provide the
  implementation evidence.
- Deferred claims: no accessibility conformance, carbon, energy or deployment
  claim is made.

## Test strategy

Focused unit tests only; no live Kafka, database or educational payloads.

| Level | Case | Acceptance criteria | Evidence expected |
|---|---|---|---|
| Unitario | Supported classified object with matching HRP-44 shape | AC-01, AC-08 | Explicit valid result; payload preserved |
| Unitario | Repeated equivalent validation | AC-02 | Identical deterministic results |
| Unitario | Input mutation guard | AC-03 | Original payload remains unchanged |
| Unitario | Non-mapping or malformed input | AC-04 | Explicit invalid result and reason |
| Unitario | Empty or wrong-domain mapping | AC-04a | `classification_mismatch` |
| Unitario | Unknown/unsupported classification | AC-05 | Explicit unsupported outcome |
| Unitario | No semantic cleaning | AC-07, AC-09 | Values are not trimmed, changed or defaulted |
| Boundary review | Scope and prohibited logic | AC-06, AC-10 | No identity, aggregation or business-key behavior |

Tests must not assert speculative email, phone, passport, IBAN, salary, IP, sex
or address rules.

## Evidence of closure

- Branch / PR: `feature/HRP-45-validation-cleaning`; PR #36 pending final approval or merge
- Review-fix commit: `13cc3f8`
- Post-fix validation: CI green; focused tests 12 passed; full suite 81 passed, 3 skipped; coverage 81.59% with the 75% threshold passed; pre-commit, validate_specs (22 files), Ruff, Ruff format, mypy and git diff --check passed.
- Jira closure comment: not applicable before review and merge
