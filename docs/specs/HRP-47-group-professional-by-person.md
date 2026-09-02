# HRP-47 - Group Professional Data by person

**Status:** Implementation-ready; pending HRP-47 human review; global identity remains unresolved  
**Owner:** Gabriela Granja
**Jira:** HRP-47  
**Branch:** `feature/HRP-47-group-professional-by-person`  
**Base:** synchronized `develop` at `c87daf7`  
**Dependencies:** HRP-24 observed contract; HRP-25 data-model boundary; HRP-43 correlation evidence; HRP-44 classification; HRP-45 validation  
**Related ADR:** `docs/adr/0006-person-correlation-key.md` (Proposed / blocked for global identity)

## Objective

Define a deterministic Professional-domain ETL grouping transformation using the
exact delivered `fullname` value as an operational bucket key. This is a
domain-local processing decision only: it does not establish global identity,
uniqueness, or a real-world person identifier.

## Context

The architecture places classification, validation and correlation in the
transformation/process stage downstream of immutable MongoDB RAW persistence.
Kafka `topic + partition + offset` is technical event provenance/idempotency, not
person identity. PostgreSQL, Redis, API and frontend concerns are downstream or
outside this pure grouping story.

HRP-46 was merged into `develop` as PR #37 and establishes the approved
architectural distinction that exact `fullname` may be used as a domain-local
operational correlation key without resolving global identity. HRP-47 applies
that precedent independently to Professional because Professional contains the
same documented candidate and no approved contract contradicts the narrow use.

This specification records the HRP-47 implementation contract. Human review of
the future implementation PR remains a lifecycle gate and is not runtime
behavior; no HRP-47 human approval is claimed here.

## Authorised evidence

- HRP-24 and `docs/02-data-contract.md` record the observed Professional-shaped
  fields as `fullname`, `company`, `company address`, `company_telfnumber`,
  `company_email` and `job`. The observed values were strings in the bounded
  sample, but apparent types do not establish formats, ranges, semantics,
  requiredness, optionality or nullability.
- HRP-44 defines the exact Professional key set:

  ```text
  {"fullname", "company", "company address", "company_telfnumber",
   "company_email", "job"} -> Professional
  ```

  Classification uses only the top-level key set and never validates business
  values.
- HRP-45 accepts a supplied classification only when it agrees with
  `classify_payload(payload)`. It performs structural validation only and does
  not clean, normalize or semantically validate values.
- HRP-43 records `fullname` as a partial correlation candidate connecting the
  Location and Professional structural shapes. It does not establish person
  identity, uniqueness, collision ground truth, completeness, normalization or
  conflict resolution.
- ADR-0006 remains Proposed and blocked for a global person-correlation key.
  Nothing in HRP-47 changes that status.

No generator source, generator log or unapproved payload evidence is used.

## Evidence classification

| Rule | Evidence source | Status |
|---|---|---|
| Professional field names and observed apparent types | HRP-24, `docs/02-data-contract.md` | OBSERVED |
| Exact Professional key-set classification | HRP-44 | CONTRACTUAL |
| Classification consistency and structural validation boundary | HRP-45 | CONTRACTUAL |
| `fullname` is a partial Location/Professional candidate | HRP-43 and authorised observation | OBSERVED |
| Exact `fullname` as a Professional operational key | HRP-46 merged precedent applied independently to Professional | ARCHITECTURAL DECISION |
| Global person identity and cross-domain aggregation | ADR-0006 | UNRESOLVED |

## Dependencies

| Dependency | Status for HRP-47 | Boundary |
|---|---|---|
| HRP-24 observed data contract | READY | Source of observed field names and apparent types |
| HRP-25 data model | PARTIAL | Documents `professional_profiles`; persistence/cardinality are not required for pure grouping |
| HRP-43 correlation evidence | PARTIAL | Establishes `fullname` as a candidate only; no identity decision |
| HRP-44 classification | READY | Exact Professional structural classification is upstream |
| HRP-45 validation | READY | Classification consistency and technical validation are upstream |
| HRP-46 Location grouping | READY precedent / NOT REQUIRED dependency | Approved sibling pattern; no runtime coupling |
| ADR-0006 | BLOCKED for global identity | Remains unresolved; not required for this domain-local operation |
| HRP-52 PostgreSQL relationship design | NOT REQUIRED | Downstream persistence/cardinality concern |
| PostgreSQL persistence | NOT REQUIRED | No persistence is implemented or specified here |
| Global person identity | BLOCKED and out of scope | Not needed for Professional-domain operational grouping |

## Scope

### Included

- A pure Professional-domain transformation after HRP-44 classification and
  HRP-45 validation.
- Explicit structural, unsupported, duplicate, ambiguity and immutability
  boundaries.
- Exact `fullname` operational grouping within the Professional domain only.
- Synthetic focused tests for the approved runtime behavior.

### Out of scope

- A global or synthetic `person_id`.
- A claim that `fullname` is globally unique or identifies a real person.
- Cross-domain correlation or aggregation with Personal, Location, Bank or Net.
- PostgreSQL, MongoDB, Redis, Kafka, API, frontend or infrastructure changes.
- Business deduplication, completeness, upserts, persistence or schema changes.
- Email, phone, salary, company, job-title or any other semantic field-value
  validation.
- Address, passport, email, phone, IBAN, composite or technical-coordinate
  fallback keys.
- Fuzzy matching, heuristic matching, trimming, case conversion or any hidden
  normalization.
- Inspecting or using the educational data generator.

## Professional structural contract

The supported Professional structure is the exact HRP-44 key set:

| Field | Structural status | Approved value interpretation |
|---|---|---|
| `fullname` | Required for exact Professional classification | Observed string shape and correlation candidate only; no identity or uniqueness claim |
| `company` | Required for exact Professional classification | Structural field only; no business-value validation |
| `company address` | Required for exact Professional classification | Structural field only; no address normalization or fallback use |
| `company_telfnumber` | Required for exact Professional classification | Structural field only; no phone validation |
| `company_email` | Required for exact Professional classification | Structural field only; no email validation |
| `job` | Required for exact Professional classification | Structural field only; no job-title validation |

No optional Professional fields are approved by the current exact-key contract.
HRP-44 ignores values; HRP-45 does not add semantic requiredness or cleaning.

## Upstream classification boundary

HRP-47 consumes the `Professional` result of HRP-44. It does not duplicate the
Professional field definition or reclassify payloads. A missing, extra, partial
or otherwise unsupported key set remains `unknown`/unsupported upstream.

## Upstream validation boundary

HRP-47 consumes only fragments that satisfy the HRP-45 boundary:

```text
classify_payload(payload) == classification
```

HRP-47 must reuse that result or contract and must not add semantic validation,
normalization, inferred values or identity logic.

## Operational grouping contract

`fullname` is the exact Professional-domain operational correlation key. This
selection is an architectural ETL decision supported by the merged HRP-46
precedent and independently applicable to Professional because the exact
Professional contract contains `fullname` and HRP-43 documents the
Location/Professional candidate relationship.

The key semantics are:

- exact string equality only;
- Professional domain scope only;
- no trimming, case folding, canonicalization or normalization;
- equal values share one operational bucket;
- different values remain in separate buckets;
- no uniqueness, identity, global, cross-domain or PostgreSQL meaning.

## Input contract

The future transformation receives an upstream processing envelope containing:

- a JSON-compatible payload (null, boolean, number, string, array or
  string-keyed object); and
- its HRP-44 classification context and HRP-45 validation result.

A supported Professional payload must be an object whose exact top-level key set
matches HRP-44 and whose supplied classification is `Professional`. Arbitrary
Python object graphs are outside this data boundary.

Structurally invalid, non-Professional, unknown or classification-inconsistent
inputs must remain explicit unsupported outcomes. The grouper must not repair or
reinterpret them.

## Output contract

The transformation returns a deterministic grouping result containing
Professional-domain groups and unresolved outcomes, with no global person
identifier. Each group contains the exact `fullname` key and distinct payload
evidence assigned to that domain-local bucket. Unresolved entries preserve the
payload and classification context and identify whether the fragment is
uncorrelated or unsupported. No persistence target is part of the result.

Each grouped fragment is represented as a `GroupedFragment` containing the payload
and one abstract, non-sensitive `source_reference` to the persisted RAW/source
event. The reference must be deterministic and stable enough for downstream
traceability, without full raw messages, PII-derived hashes, secrets or generator
information. The concrete reference form is delegated to the ingestion/raw-
persistence contract. This amendment preserves Professional's exact `fullname`
grouping, duplicate semantics and unresolved behavior; it does not add a
cross-domain correlation rule.

## Result states

The result uses these states:

- `grouped`: one operational bucket with one distinct payload value;
- `ambiguous`: one operational bucket containing multiple distinct payloads;
- `uncorrelated`: an accepted Professional payload has an empty, null,
  non-string or otherwise unusable `fullname` value;
- `unsupported`: the input is malformed, not Professional, unknown, or failed
  the HRP-44/HRP-45 boundary.

These states do not describe global identity or business validity.

## Invariants

- HRP-44 remains the only source of the Professional structural field set.
- HRP-45 remains the only upstream structural validation boundary.
- No semantic value validation or normalization is performed.
- No global or synthetic person identifier is created.
- No cross-domain relationship is inferred.
- No fallback field, fuzzy match or heuristic is used.
- Distinct evidence is never silently discarded.
- Input payloads and classification context remain unchanged.
- Persistence and infrastructure remain outside HRP-47.

## Duplicate/replay behavior

Technical Kafka coordinates remain event provenance/idempotency and are not a
Professional grouping key. Exact repeated JSON payload evidence is represented
once within a bucket. This is transformation-level deduplication, not global
business deduplication.

## Missing/unusable correlation behavior

A structurally missing `fullname` means the payload does not satisfy the exact
Professional structure and must be reported as `unsupported` by the upstream
classification/validation boundary. HRP-47 must not reinterpret it as a valid
Professional fragment.

An accepted Professional payload whose present `fullname` value is empty, null,
non-string or otherwise unusable receives `uncorrelated`. A missing required
structural field remains `unsupported`; it is not reinterpreted as an
uncorrelated value. No value is inferred and no fallback field is selected.

## Ambiguity/collision behavior

Equal exact `fullname` values share one Professional operational bucket without
implying that the fragments represent the same person. Different exact values
produce separate buckets. Multiple distinct payloads under one exact key remain
preserved and make the group `ambiguous`.
No address, company, email, phone, passport, IBAN or composite value resolves a
collision.

## Conflicting evidence behavior

Conflicting Professional attributes under one approved operational key are
preserved as distinct evidence and reported explicitly as ambiguity. No
precedence rule, latest-value rule, silent merge or silent discard is authorized.

## Ordering/determinism

The result must be independent of input order. Groups, payload evidence
and unresolved outcomes must have a deterministic documented order under the
JSON-compatible input contract. Exact duplicate handling must be repeatable.

## Input immutability

The transformation reads payloads and classification context without mutation. MongoDB RAW,
Kafka records, HRP-44 results and HRP-45 results are not modified by HRP-47.

## Unsupported input behavior

Unknown classification, a non-Professional supported classification, malformed
JSON-compatible input, an incomplete or extra-key mapping, or a classification
that disagrees with `classify_payload(payload)` is returned explicitly as
unsupported. HRP-47 does not repair, coerce or remap the input.

## Global identity boundary

HRP-47 does not create, infer or persist a global person identity. `fullname` is
only a Professional-domain operational key. It is not globally unique, not a
real-person identifier, not a cross-domain key, and not evidence that equal
values represent the same person.

ADR-0006 remains Proposed/blocked. Global correlation, business uniqueness,
person completeness and cross-domain aggregation remain unresolved.

## Persistence boundary

HRP-47 is a pure transformation/grouping story. MongoDB RAW remains immutable;
Kafka ingestion is unchanged; Redis state, PostgreSQL tables/upserts, APIs and
infrastructure are downstream concerns. HRP-52 and a PostgreSQL target are not
technical prerequisites for implementing this pure grouper.

## Acceptance criteria

These are runtime criteria for the implementation described by this
specification. They do not establish global identity or uniqueness.

- [ ] **AC-01:** An exact HRP-44 Professional payload accepted by HRP-45 is
  retained as Professional input without semantic validation or mutation.
- [ ] **AC-02:** Equal exact `fullname` values share one Professional-domain
  bucket and different exact values remain in separate buckets.
- [ ] **AC-03:** Exact duplicate payloads are represented once, and equivalent
  input produces the same result independently of input order.
- [ ] **AC-04:** A structurally missing `fullname` is returned as `unsupported`;
  an accepted Professional payload with an unusable present `fullname` is
  returned as `uncorrelated`, without inference or fallback.
- [ ] **AC-05:** Distinct payloads under one operational key are all preserved and
  the result is explicitly `ambiguous`.
- [ ] **AC-06:** Unknown, unsupported, malformed, non-Professional or
  classification-inconsistent input produces an explicit `unsupported` outcome.
- [ ] **AC-07:** Payloads and classification context remain unchanged, and no
  Kafka, RAW, HRP-44 or HRP-45 behavior is modified.
- [ ] **AC-08:** No normalization, fuzzy matching, fallback correlation, global
  `person_id`, cross-domain aggregation or persistence coupling is introduced.

## Test strategy

Focused unit tests must use synthetic JSON-compatible fixtures only and reference
the AC identifiers in behavior-oriented names or docstrings.

| Case | Acceptance criteria | Proposed test name | Behavior proven |
|---|---|---|---|
| Valid exact Professional structure | AC-01 | `test_valid_professional_payload_is_retained_ac01` | Payload is retained; no semantic validation or mutation |
| Exact approved operational key | AC-02 | `test_same_and_different_approved_keys_define_domain_local_groups_ac02` | Same key groups; different key separates |
| Duplicate and reordered input | AC-03 | `test_duplicate_professional_payloads_are_deterministic_ac03` | One exact duplicate; stable result under reversal |
| Structurally missing key | AC-04, AC-06 | `test_missing_professional_key_is_unsupported_ac04` | Upstream-style explicit `unsupported` outcome |
| Unusable accepted key | AC-04 | `test_unusable_professional_key_is_uncorrelated_ac04` | Explicit `uncorrelated` outcome; no fallback |
| Distinct same-key evidence | AC-05 | `test_distinct_same_key_professional_evidence_is_ambiguous_ac05` | All payloads preserved; explicit ambiguity |
| Unknown/malformed/non-Professional input | AC-06 | `test_unsupported_professional_input_is_explicit_ac06` | Explicit unsupported outcome |
| Payload/classification immutability and boundary audit | AC-07, AC-08 | `test_professional_grouping_preserves_boundaries_ac07_ac08` | No mutation, identity, persistence or external coupling |

No test may assert global uniqueness, real-person identity or a correlation rule
that has not been approved. No test may use generator data or logs.

## Definition of Ready

HRP-47 is ready for production implementation because the Professional structural
contract, upstream boundaries and exact domain-local grouping semantics are
defined by the approved contracts and merged HRP-46 precedent. HRP-44 and HRP-45
remain the upstream contracts, persistence remains separate, and ADR-0006 remains
Proposed/blocked for global identity.

Human approval is a readiness/governance gate, not runtime component behavior.

## Definition of Done

- The approved operational decision is reflected in this specification.
- The smallest sibling Professional grouper implementation matches the approved
  contract.
- Focused synthetic behavior tests cover every runtime acceptance criterion.
- Relevant specification, lint, format, type and test gates pass.
- Human review occurs before commit, push, PR merge or Jira closure.

## Risks and limitations

- HRP-43 provides candidate evidence, not identity ground truth or uniqueness.
- Equal `fullname` values may represent different people; different values may
  represent the same person. A local bucket must not be described otherwise.
- Professional values may be missing, malformed or semantically invalid without
  violating the currently structural HRP-44/HRP-45 boundary.
- A future ADR-0006 decision may change cross-domain aggregation or persistence
  design; HRP-47 must not anticipate it.
- HRP-47 uses the approved narrow domain-local pattern; this does not authorize
  global identity or cross-domain aggregation.

## Shared-abstraction recommendation

Implement Professional grouping as a separate sibling transformation. HRP-46 is
an approved architectural precedent, not a runtime dependency, and its Location
payload schema must not be copied automatically. A future generic abstraction may
be considered only after both domain contracts demonstrate genuinely shared
semantics; no refactor is part of HRP-47.

## Traceability

```text
Jira HRP-47
  -> this specification
  -> HRP-24 observed contract / HRP-25 boundary
  -> HRP-44 Professional classification
  -> HRP-45 structural validation
  -> exact Professional `fullname` operational grouping
  -> sibling transformation and focused tests
  -> ADR-0006 global identity remains Proposed/blocked
```

## ADR impact

No change to ADR-0006 is required. HRP-47 applies a narrow domain-local ETL
decision and does not change ADR-0006's global status. A new ADR is required only
if the scope expands to global identity, cross-domain aggregation, durable
business uniqueness or an irreversible persistence rule.

## Accessibility and sustainability applicability

- Accessibility: not applicable - this is a backend transformation contract with
  no user-facing flow.
- Sustainability: applicable at implementation time - the operation must
  remain pure, bounded, deterministic and free of unnecessary persistence or
  transfer; no measured efficiency claim is made here.
- Deferred claims: no accessibility conformance, carbon, energy or deployment
  claim is made.

## Evidence and status

- Branch: `feature/HRP-47-group-professional-by-person`
- Base: synchronized `develop` at `c87daf7`
- Specification: finalized; implementation added and pending human review
- Production implementation: `src/hr_pro_platform/transformation/professional_grouper.py`
- Focused tests: `tests/unit/test_professional_grouper.py` (8 tests)
- PR: #38 — current evidence shows green governance checks, labels and quality checks
- Commits:
  - `3ea1f51` — docs(HRP-47): define professional grouping specification
  - `f56b262` — feat(HRP-47): group Professional fragments by exact fullname
  - `ac31a8b` — test(HRP-47): cover deterministic professional grouping
- Jira closure: PENDING until merge and the final evidence comment
- Validation: `python scripts/validate_specs.py` passed for 24 specification
  files; focused HRP-47 tests passed (8); full pytest passed (98 passed, 3
  skipped: PostgreSQL environment unavailable); targeted Ruff and format checks
  passed; mypy passed for 19 source files; `git diff --check` passed.
  Repository-wide Ruff traversal was blocked by inaccessible local paths, so
  the valid source check was run on the changed source and test files. Isolated
  pre-commit was attempted but could not fetch hook environments because the
  network was unavailable. Current PR #38 evidence covers governance checks,
  labels and quality checks; merge, human approval, Jira closure and release
  completion are not claimed.
