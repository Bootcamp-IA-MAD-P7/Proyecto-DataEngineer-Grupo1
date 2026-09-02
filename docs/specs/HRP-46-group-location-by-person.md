# HRP-46 - Group Location by person

**Status:** Blocked - specification draft pending human review
**Owner:**
**Jira:** HRP-46
**Dependencies:** HRP-34 raw persistence boundary; HRP-44 domain classification; HRP-45 validation boundary; HRP-43 correlation evidence
**Related ADR:** `docs/adr/0006-person-correlation-key.md` (Proposed / blocked)

## Objective

Define the contract required to group Location fragments by person without
inventing a person key, treating an observed field as globally unique, or
crossing the unresolved identity boundary.

This specification does not authorize implementation yet. The current evidence
is insufficient to define a defensible grouping rule.

## Context and authorized evidence

The approved contract identifies Location fragments structurally through HRP-44:

```text
{"fullname", "city", "address"} -> Location
```

HRP-43 and ADR-0006 establish that `fullname` and `address` are correlation
candidates only. HRP-43 found partial observable relationships, but no ground
truth for person identity, uniqueness, completeness or conflict resolution.
Specifically, `address` supports only a partial Location/Net connection in the
authorized sample; this does not establish that equal addresses identify the same
person or that different addresses identify different people.

The technical Kafka identity `topic + partition + offset` is event idempotency
provenance, not person identity. MongoDB RAW remains immutable evidence and is
not modified by this story.

## Architectural boundary

If later authorized, this capability belongs in the transformation/process stage,
downstream of RAW persistence, HRP-44 classification and HRP-45 validation. It
must not change Kafka ingestion, MongoDB RAW persistence, the HRP-44 classifier or
the HRP-45 validator. PostgreSQL serving persistence and API behavior are outside
this story unless a separately approved integration contract requires them.

## Scope

### Potentially included after the identity gate is resolved

- Processing structurally supported and HRP-45-validated Location fragments.
- Applying an explicitly approved Location grouping key and conflict policy.
- Deterministic handling of duplicates, incomplete fragments, ordering and
  reprocessing according to that approved policy.
- Explicit outcomes for grouped, ungrouped, ambiguous, conflicting and unsupported
  inputs.

### Explicitly excluded now

- A global `person_id` or synthetic identity derived by this story.
- Assuming `fullname`, `address`, `passport` or any composite is unique.
- Fuzzy matching, heuristic matching, fallback keys or precedence rules.
- Cross-domain correlation with Personal, Professional, Bank or Net fragments.
- Person completeness, global aggregation, business deduplication or PostgreSQL
  business-key upserts.
- Changes to ingestion, RAW persistence, classification, validation, Redis,
  serving APIs or infrastructure.

## Current contract gate

The story title alone does not authorize a meaning for “by person”. The approved
evidence does not currently distinguish these possibilities:

1. domain-local Location grouping;
2. cross-domain person correlation; or
3. global person aggregation.

The narrower hypothesis “group Location fragments using only correlation
established within authorized Location evidence” is not adopted by this spec:
the evidence does not establish a Location-only identity key, uniqueness,
collision behavior or person ground truth. It requires explicit human approval
and a documented correlation contract before implementation.

## Required input and output contract (pending approval)

The eventual implementation must receive a structurally classified and HRP-45
validated Location fragment plus the approved correlation context. The exact
correlation context is undefined until ADR-0006 or a separately approved
domain-local decision authorizes it.

The eventual result must make the outcome explicit, at minimum distinguishing:

- grouped using an approved key;
- uncorrelated fragment;
- ambiguous correlation;
- conflicting evidence;
- incomplete fragment;
- duplicate/replay outcome; and
- unsupported or invalid input.

No concrete grouping key, result schema, persistence target or conflict policy is
approved by this specification.

## Behavior boundaries

Until the identity decision is approved:

- no Location fragment may be merged into a person record;
- no equality of `fullname` or `address` may be treated as proof of identity;
- no conflicting evidence may be silently discarded;
- incomplete or out-of-order fragments may be retained for later processing only
  under an approved technical policy, without claiming person membership;
- technical duplicate detection may use `topic + partition + offset` only within
  the existing raw idempotency boundary;
- unknown HRP-44 structures and HRP-45 invalid results must remain explicit; and
- no output may imply a global person identity.

## Dependencies and blockers

The implementation is blocked by the unresolved correlation decision in
ADR-0006. Before implementation, the owning decision must define:

1. whether this story permits domain-local grouping;
2. the approved key or correlation mechanism;
3. uniqueness and collision assumptions;
4. conflict resolution;
5. completeness and incomplete-fragment behavior;
6. duplicate and replay semantics at the business level.

Persistence of a grouping result is a separate downstream integration concern.
An unresolved PostgreSQL or other persistence target does not by itself block a
pure grouping transformation once the grouping contract is approved. Any
persistence integration requires its own approved contract and task boundary.

Evidence required for a person-level decision is specified by HRP-43 and
ADR-0006. It must be authorized, privacy-safe and reviewed by a human; generator
source or logs are not permitted.

## Acceptance criteria

- [ ] **AC-01:** The specification identifies HRP-44 classification and HRP-45
  validation as upstream boundaries without redefining either responsibility.
- [ ] **AC-02:** The specification states that no grouping key is currently
  authorized and that `fullname` and `address` remain correlation candidates only.
- [ ] **AC-03:** No global `person_id`, synthetic identity, uniqueness rule,
  fallback heuristic or cross-domain correlation is introduced.
- [ ] **AC-04:** Technical event idempotency is kept separate from business/person
  deduplication.
- [ ] **AC-05:** The future contract defines explicit grouped, uncorrelated,
  ambiguous, conflicting, incomplete, duplicate and unsupported outcomes before
  implementation.
- [ ] **AC-06:** The future behavior preserves RAW immutability and does not change
  Kafka ingestion, classification, validation, serving or API boundaries.
- [ ] **AC-07:** Synthetic tests, linked to the approved future grouping contract,
  cover deterministic behavior, duplicates, incomplete and out-of-order input,
  ambiguity, conflicts, unsupported input and input immutability.

## Test strategy

No production tests or implementation are authorized by this blocked draft.
After the identity gate is resolved, focused unit tests should use synthetic
fixtures and reference AC identifiers. They must cover the approved behavior for:

| Case | Required evidence |
|---|---|
| Valid Location fragment | Accepted only under the approved grouping contract |
| Deterministic repeated processing | Same approved input produces the same result |
| Technical duplicate/replay | No duplicate operation under the approved idempotency policy |
| Incomplete fragment | Explicit outcome; no invented values or identity |
| Out-of-order fragment | Explicit outcome under the approved ordering policy |
| Ambiguous correlation | No silent merge; explicit ambiguity |
| Conflicting evidence | Explicit conflict policy; no silent discard |
| Unsupported/unknown input | Explicit non-grouped outcome |
| Input immutability | Payload and technical metadata remain unchanged |
| Identity boundary | No global identity or unapproved key appears in output |

Integration, E2E and database tests are deferred until a downstream persistence
contract exists. Pure grouping tests remain separate from that persistence gate.
No test may infer uniqueness from the absence of collisions in an observed or
synthetic sample.

## Definition of Ready

HRP-46 is ready for implementation only when:

- a human-approved identity scope exists;
- the grouping key/mechanism and conflict/completeness policies are documented;
- the domain-local/global identity decision is recorded in ADR-0006 or an
  explicitly approved related artifact;
- dependencies on HRP-43, HRP-44 and HRP-45 are explicit;
- acceptance criteria define observable outcomes; and
- the pure grouping test cases are approved.

Any downstream persistence integration is governed by a separate approved
contract and is not a prerequisite for the pure grouping transformation.

## Definition of Done

When implementation is authorized, completion requires the approved result in
the task branch, focused behavior tests, relevant documentation and quality-gate
evidence. Human review, PR approval, merge and Jira closure remain separate
required workflow steps. This blocked specification is not a completion claim.

## Accessibility and sustainability applicability

- Accessibility: not applicable - this is a backend transformation contract with
  no user-facing flow.
- Sustainability: applicable at implementation time - grouping must be bounded,
  deterministic and avoid duplicate processing or unbounded temporary state. No
  efficiency claim is made before an implementation and measured evidence exist.
- Deferred claims: no accessibility conformance, carbon, energy or deployment
  claim is made.

## Traceability

```text
Jira HRP-46
  -> this specification
  -> future transformation implementation and behavior tests
  -> HRP-43 evidence / HRP-44 classifier / HRP-45 validator
  -> ADR-0006 decision before person grouping is authorized
```

## Risks and unresolved questions

- The story title may conceal a global identity requirement.
- A domain-local Location rule could still encode unsupported uniqueness.
- `address` may represent a shared or changing location; the current evidence
  does not resolve that meaning.
- `fullname` may be non-unique; no collision ground truth is available.
- Business duplicates, completeness and ordering remain undefined.

## Evidence and status

- Branch: `feature/HRP-46-group-location-by-person`
- Base: synchronized `develop` at `f608156` when this branch was created
- Implementation: not started
- Validation: `python scripts/validate_specs.py` passed for 23 specification files; `git diff --check` passed
- PR / commit / Jira closure: not created or authorized
