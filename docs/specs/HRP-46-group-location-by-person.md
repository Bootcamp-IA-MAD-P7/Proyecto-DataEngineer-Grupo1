# HRP-46 - Group Location by person

**Status:** Implemented - pending human review; global identity remains unresolved
**Owner:** Gabriela
**Jira:** HRP-46
**Dependencies:** HRP-34 raw persistence boundary; HRP-44 domain classification; HRP-45 validation boundary; HRP-43 correlation evidence
**Related ADR:** `docs/adr/0006-person-correlation-key.md` (global identity Proposed / blocked)

## Objective

Define and implement a deterministic Location-only operational grouping
transformation using the exact delivered `fullname` value as its bucket key.
This operational key is not a global person identifier and does not claim that
equal values identify the same real-world person.

## Context and decision under review

HRP-44 identifies the supported Location shape as:

```text
{"fullname", "city", "address"} -> Location
```

HRP-43 and ADR-0006 establish that `fullname` and `address` are correlation
candidates only and do not prove global identity or uniqueness. PR #37 proposes
`fullname` for HRP-46 as an exact, domain-local operational grouping value under
those known limitations and requests human review and approval. This is an ETL
architecture decision under review, not new empirical evidence.

The technical Kafka identity `topic + partition + offset` remains event
provenance/idempotency, never person identity.

## Scope and boundaries

### Included

- Location fragments already structurally classified by HRP-44 and accepted by
  HRP-45.
- Exact `fullname` bucket grouping within the Location domain only.
- Deterministic repeated-evidence handling and input-order independence.
- Explicit grouped, uncorrelated, ambiguous and unsupported outcomes.

### Excluded

- Global `person_id`, real-world identity, cross-domain correlation or aggregation.
- Treating `fullname` as globally unique or proven unique.
- `address`, `passport`, email, telephone, IBAN or any composite fallback.
- Fuzzy matching, heuristic matching, precedence rules or undocumented defaults.
- Silent conflict resolution or silent evidence loss.
- Kafka ingestion, MongoDB RAW mutation, HRP-44 classification changes or HRP-45
  validation changes.
- PostgreSQL, Redis, API, frontend or infrastructure persistence.

## Input contract

The public transformation API is:

```text
group_location_fragments(
    fragments: Iterable[ClassifiedFragment],
) -> LocationGroupingResult
```

`ClassifiedFragment` contains a processing envelope with a JSON-compatible
payload (null, boolean, number, string, array or object with string keys) and its
upstream classification context. A supported payload must be a Location-shaped
mapping and must have passed HRP-44 and HRP-45. The grouping boundary may reuse
those existing contracts to report unsupported or invalid input; it must not
duplicate their field or semantic rules. Arbitrary Python object graphs are
outside this contract.

## Output contract

`LocationGroupingResult` contains deterministic operational groups keyed by exact
`fullname`, plus unresolved entries. A group has:

- `key`: the exact `fullname` string;
- `status`: `grouped` or `ambiguous`; and
- `fragments`: distinct payloads preserved in the group.

Unresolved entries have one of these states:

- `uncorrelated`: a structurally valid Location payload has an empty or
  non-string `fullname` value;
- `unsupported`: the fragment is not a supported Location input or fails an
  upstream boundary.

Identical repeated evidence is represented once. Distinct conflicting payloads
remain present and are not silently resolved or discarded. Results are
independent of input order. No global person identifier is created and no
persistence target is owned by this story.

## Grouping semantics

- Equal exact `fullname` values share one operational Location bucket.
- Different exact `fullname` values produce different operational buckets.
- The key is not trimmed, case-folded, canonicalized or otherwise normalized.
- A structurally missing `fullname` fails the supported Location shape and is
  returned as `unsupported`; an accepted Location payload with an empty or
  non-string value receives no fabricated key and is returned as `uncorrelated`.
- Exact repeated payloads in a bucket are represented once.
- Distinct payloads under one key are all preserved and the group is marked
  `ambiguous`; neither payload is silently selected or discarded.
- Input order does not change the semantic result. Groups and fragment entries
  are returned deterministically.
- Deterministic ordering uses canonical JSON serialization; no arbitrary-object
  `repr` fallback is part of the supported contract.
- Incomplete or structurally unsupported input is returned explicitly as
  `unsupported`; no business value is inferred.
- Persistence of the result is a separate downstream integration concern.

## Identity limitation

`fullname` is a domain-local operational correlation key for HRP-46 only. It is
not globally unique, is not `person_id`, is not a cross-domain key and does not
prove real-world identity. ADR-0006 remains Proposed/blocked for global identity,
business uniqueness and person-level aggregation.

## Acceptance criteria

- [ ] **AC-01:** A valid Location fragment with a non-empty string `fullname` is
  placed in the group keyed by that exact value.
- [ ] **AC-02:** Equal exact keys share one operational Location group and
  different keys produce different groups without a global identity claim.
- [ ] **AC-03:** Exact repeated payloads are emitted once, and grouping is
  deterministic and independent of input order.
- [ ] **AC-04:** A structurally missing `fullname` produces an explicit
  `unsupported` outcome through the upstream boundary. An accepted Location
  payload with an empty or non-string `fullname` produces `uncorrelated`, with
  no fabricated or fallback key.
- [ ] **AC-05:** Distinct payloads under one key are preserved and the group is
  marked `ambiguous` without silent conflict resolution or data loss.
- [ ] **AC-06:** Unsupported classification, malformed input or failed upstream
  validation produces an explicit `unsupported` outcome.
- [ ] **AC-07:** The payload and classification context remain unchanged, and the
  transformation does not modify RAW data, Kafka ingestion, HRP-44 or HRP-45
  behavior.
- [ ] **AC-08:** No address/passport/cross-domain/fuzzy/fallback correlation or
  global `person_id` is created, and persistence remains outside this story.

## Test strategy

Focused unit tests use synthetic fixtures and reference AC identifiers:

| Case | Acceptance criteria | Evidence |
|---|---|---|
| Valid Location fragment | AC-01 | Exact `fullname` bucket |
| Same and different keys | AC-02 | Expected operational groups |
| Duplicate and reordered input | AC-03 | Stable deduplicated result |
| Missing structural key | AC-04 | `unsupported` via upstream boundary |
| Unusable accepted key | AC-04 | `uncorrelated` outcome |
| Conflicting same-key values | AC-05 | `ambiguous`, all distinct payloads preserved |
| Unsupported/invalid input | AC-06 | `unsupported` outcome |
| Payload/classification immutability and boundaries | AC-07, AC-08 | No mutation or identity leakage |

No test may assert global uniqueness or use `address`, `passport`, email,
telephone, IBAN, fuzzy matching or an invented fallback key.

## Definition of Ready

PR #37 proposes the Location-only exact `fullname` operational decision for
human review and approval. Until approval is recorded, the implementation remains
pending review. Global identity remains a separate blocked decision. Any
downstream persistence integration requires its own approved contract and is not
a prerequisite for this pure grouping transformation.

## Definition of Done

- The implementation matches this specification and preserves all explicit
  identity and persistence boundaries.
- Every runtime Acceptance Criterion has focused synthetic test evidence.
- Specification validation, lint, formatting, type and relevant test gates pass.
- Human review occurs before commit, push, PR merge or Jira closure.

## Accessibility and sustainability applicability

- Accessibility: not applicable - this is a backend transformation with no
  user-facing flow.
- Sustainability: applicable - grouping is bounded, deterministic and avoids
  duplicate output/state; no measured efficiency claim is made.
- Deferred claims: no accessibility conformance, carbon, energy or deployment
  claim is made.

## Traceability

```text
Jira HRP-46
  -> this specification
  -> HRP-44 classification -> HRP-45 validation -> HRP-46 grouping
  -> implementation and focused tests
  -> ADR-0006 global identity limitation
```

## Evidence and status

- Branch: `feature/HRP-46-group-location-by-person`
- Base: synchronized `develop` at `f608156`
- Implementation: complete in the working tree; pending human review
- PR: #37; human review requested; reviewer reports checks green and branch mergeable
- Commits: `ee1d695` (specification), `e4d52fe` (local correlation boundary), `8f2d03e` (implementation), `8cceb78` (tests)
- Validation: focused HRP-46 tests 9 passed; full pytest 90 passed, 3 skipped; coverage 83.17% with the 75% threshold passed; `validate_specs` 23 specification files passed; Ruff check passed; Ruff format check passed with 147 files already formatted when unrelated inaccessible/local cache paths were excluded; mypy passed for 18 source files; `git diff --check` passed
- CI: PR #37 reviewer reports checks green and branch mergeable; individual CI job names/statuses are not recorded here
- Jira closure: pending; not claimed by this PR
