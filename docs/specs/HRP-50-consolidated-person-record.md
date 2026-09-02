# HRP-50 - Consolidated person record

**Status:** Specification draft; pending human review
**Jira:** HRP-50 - Crear un único registro final por persona
**Owner:** Gabriela Granja
**Related ADR:** [`docs/adr/0006-person-correlation-key.md`](../adr/0006-person-correlation-key.md)
**Dependencies:** HRP-46, HRP-47, HRP-48, HRP-49, HRP-61 and the approved source-provenance input contract

## Context

The transformation layer currently groups fragments independently by domain-local
operational keys. HRP-50 assembles those grouped results into one operational
consolidated record for each connected component formed by the exact relationships
approved in ADR-0006.

This specification defines a transformation contract only. It does not establish
real-world identity, a universal natural key, persistence identity or PostgreSQL
behavior. The authorized correlation evidence is bounded and aggregate; it does not
prove identity, completeness, uniqueness or the absence of future collisions.

No educational generator source, implementation artifact, fixture, notebook, log or
new RAW discovery is required or authorized for this task.

## Objective

Define a pure, deterministic transformation that:

- consumes already-grouped Personal, Location, Professional, Bank and Net fragments;
- applies only the approved ADR-0006 exact correlation edges;
- builds one consolidated operational record per connected component;
- preserves contributing fragments and source provenance;
- records the exact correlation rules used; and
- exposes incomplete, ambiguous and unresolved outcomes without silently merging or
  discarding evidence.

## Scope

Included:

- cross-domain assembly of existing grouped results;
- exact, transitive operational correlation;
- consolidated transformation-record shape;
- domain-fragment, rule-traceability and source-provenance contracts;
- deterministic ordering and status semantics;
- unit and contract/integration acceptance criteria for consolidation.

## Out of scope

HRP-50 does not define or implement:

- detailed duplicate or replay resolution;
- late-event reconciliation;
- detailed out-of-order event handling;
- content-conflict precedence or update policy;
- retry/recovery semantics;
- PostgreSQL schema, PK/FK/indexes, INSERT/UPDATE/UPSERT or `ON CONFLICT`;
- persistence identity semantics or a global `person_id`;
- Kafka consumer behavior or performance;
- API, frontend, Docker or infrastructure behavior;
- generator behavior.

These boundaries are consistent with the architecture, ADR-0006 and the planned
HRP-51 responsibility.

## Dependencies

| Dependency | Required contract | Current state |
|---|---|---|
| ADR-0006 | Four approved exact edges and identity limitations | Merged and accepted in principle; human acceptance gate must remain satisfied |
| HRP-46 | Location grouping by exact `fullname` | Existing grouped output; payload-only provenance gap |
| HRP-47 | Professional grouping by exact `fullname` | Existing grouped output; payload-only provenance gap |
| HRP-48 | Bank grouping by exact `passport` | Existing grouped output; payload-only provenance gap |
| HRP-49 | Net grouping by exact `address` | Existing grouped output; payload-only provenance gap |
| HRP-61 | Personal grouping by exact `passport` | Existing grouped output; payload-only provenance gap |
| Source provenance | An abstract non-sensitive reference for every contributing source fragment | Defined at transformation level; concrete raw-persistence form remains delegated |

The existing groupers must not be refactored as part of this specification task. If
their output types cannot supply the required provenance, implementation must first
make the smallest deliberately reviewed contract change needed to provide it.

## Current grouped-input contracts

| Domain | Current module and function | Current result | Local grouping key | Current fragment representation | Current provenance |
|---|---|---|---|---|---|
| Location | `transformation/location_grouper.py` / `group_location_fragments` | `LocationGroupingResult` | Exact `fullname` | `LocationGroup.fragments: tuple[JSONPayload, ...]` | Payload only; no Kafka coordinates or raw-event reference |
| Professional | `transformation/professional_grouper.py` / `group_professional_fragments` | `ProfessionalGroupingResult` | Exact `fullname` | `ProfessionalGroup.fragments: tuple[JSONPayload, ...]` | Payload only; no Kafka coordinates or raw-event reference |
| Bank | `transformation/bank_grouper.py` / `group_bank_fragments` | `BankGroupingResult` | Exact `passport` | `BankGroup.fragments: tuple[JSONPayload, ...]` | Payload only; no Kafka coordinates or raw-event reference |
| Net | `transformation/net_grouper.py` / `group_net_fragments` | `NetGroupingResult` | Exact `address` | `NetGroup.fragments: tuple[JSONPayload, ...]` | Payload only; no Kafka coordinates or raw-event reference |
| Personal | `transformation/personal_grouper.py` / `group_personal_fragments` | `PersonalGroupingResult` | Exact `passport` | `PersonalGroup.fragments: tuple[JSONPayload, ...]` | Payload only; no Kafka coordinates or raw-event reference |

The current modules independently define similar `ClassifiedFragment` types. Their
group records do not expose classification context or source metadata, and their
unresolved result shapes are not identical. HRP-50 must consume an explicitly
approved input contract rather than silently assuming these differences are resolved.
The affected domain specifications now require provenance-bearing grouped fragments
for downstream HRP-50 use; their domain-local grouping semantics remain unchanged.

## Correlation rules

ADR-0006 is the architectural source of truth. HRP-50 may use only these exact raw
equality edges:

| Stable rule identifier | ADR-0006 relationship |
|---|---|
| `personal_bank_passport` | `Personal.passport == Bank.passport` |
| `personal_location_fullname` | `Personal.name + " " + Personal.last_name == Location.fullname` |
| `location_professional_fullname` | `Location.fullname == Professional.fullname` |
| `location_net_address` | `Location.address == Net.address` |

Comparison is exact raw equality. HRP-50 applies no trimming, whitespace collapsing,
case folding, diacritic normalization, fuzzy matching, heuristic matching or
undocumented fallback. Transitivity is permitted only through these four edges.

These relationships are project-level operational correlation. They do not prove
real-world identity, universal uniqueness or a natural identity key. Absence of an
edge is not proof that two fragments belong to different real-world people.

HRP-50 does not create or assign persistence semantics to `person_id`.

## Source provenance contract

ADR-0006 requires traceability of every contributing source/domain fragment. The
current grouped outputs do not provide that capability, so implementation cannot
claim complete traceability without an approved input-contract change.

The minimum `SourceReference` capability is:

- identify one source fragment deterministically and unambiguously within the
  authorized source boundary;
- remain stable while the same source evidence is reprocessed;
- be carried with each domain fragment into the consolidated record;
- support deterministic ordering and audit lookup without embedding the raw event;
- contain no full payload, PII-derived hash, secret, generator information or other
  unnecessary sensitive material.

The reference may be based on existing RAW/document metadata if the existing
architecture and repository contracts confirm that choice. Kafka
`topic`/`partition`/`offset` is one possible implementation, but this specification
does not force it because the current HRP-50 input contracts do not establish it as
the required final reference field.

The concrete storage form is delegated to the ingestion/raw-persistence contract.
HRP-50 therefore does not choose Kafka coordinates, Mongo `_id`, UUIDs or hashes.
The amended grouped-output contracts require this abstract capability before
implementation; the current committed implementations remain payload-only until
their implementation work is deliberately updated.

## Consolidated output contract

The transformation-level result is:

```text
ConsolidationResult
  records: tuple[ConsolidatedPersonRecord, ...]
  unresolved: tuple[UnresolvedContribution, ...]

ConsolidatedPersonRecord
  domains:
    personal: DomainContribution | null
    location: DomainContribution | null
    professional: DomainContribution | null
    bank: DomainContribution | null
    net: DomainContribution | null
  status: complete | incomplete | ambiguous
  correlation_rules: tuple[str, ...]
  provenance: tuple[SourceReference, ...]

DomainContribution
  fragments: tuple[GroupedFragment, ...]

UnresolvedContribution
  payload: JSON-compatible value
  context: upstream classification/context when available
  source_reference: SourceReference when available
  reason: technical reason
```

`DomainContribution` contains the grouped fragment evidence for one domain and its
source references. Domain payloads may naturally contain business data because they
are the transformation data being consolidated. Provenance and correlation metadata
must not create extra copies of sensitive identity fields.

The five domain fields are explicit and deterministic. A missing domain is `null`; no
value is fabricated. A component may contain multiple grouped fragments from one
domain only when the input contract establishes that this is non-ambiguous. If
multiple same-domain groups or fragments make the component operationally ambiguous,
all evidence is retained and the record status is `ambiguous`.

Unresolved inputs are not silently dropped. They are returned in
`ConsolidationResult.unresolved`, outside `records`, through an explicit
`UnresolvedContribution` representation preserving the available payload, context
and source reference. This follows the existing `groups` plus `unresolved` pattern
used by the domain groupers and does not perform HRP-51 reconciliation.

`correlation_rules` contains an ordered tuple of the stable rule identifiers actually
used to connect the component. It must not store passport, name, fullname or address
values merely for convenience. `source_references` is the canonical ordered union of
the references carried by all `GroupedFragment` values in the record.

No SQL table, database key, upsert operation or global business identifier is defined
here.

## Status model

HRP-50 identifies and represents the following states:

- `complete`: all five domains are present, the component has no unresolved or
  ambiguous contribution, and every contributing fragment has valid provenance.
- `incomplete`: correlation is operationally usable and unambiguous, but one or more
  domains are absent. Missing domains are represented as `null`.
- `ambiguous`: the connected component contains conflicting or multiple same-domain
  grouped evidence such that HRP-50 cannot represent one unambiguous contribution for
  that domain. All evidence remains present; no precedence is applied.
Unresolved material is not a `ConsolidatedPersonRecord.status`; it is an entry in
`ConsolidationResult.unresolved` when an input cannot participate in an approved
operational component because required correlation data or structure is unavailable.
A missing implementation capability such as provenance is a contract blocker, not a
reason to emit a misleading consolidated record.

Deterministic status precedence for records is:

```text
ambiguous > incomplete > complete
```

This precedence only describes transformation output. HRP-51 will define any future
resolution, reconciliation, late-arrival or update behavior.

## Assembly semantics

The design sequence is:

```text
grouped domain fragments
  -> approved exact ADR-0006 edges
  -> connected operational components
  -> one consolidated record per component
  -> domain contributions and provenance
  -> correlation trace
  -> consolidation status
```

The transformation must:

- produce one output record per operational connected component;
- use only the four approved edges;
- preserve partial-domain components;
- keep unrelated components separate;
- preserve ambiguous and unresolved evidence explicitly;
- order domains, contributions, rules and source references canonically;
- produce equivalent output for equivalent inputs in different iteration orders; and
- avoid mutating caller-provided mappings, fragments or grouping results.

No graph algorithm or production implementation is introduced by this specification.

## Security and privacy boundary

Correlation traceability uses stable rule identifiers, not copied identity values.
Source provenance must not contain full raw messages, PII-derived hashes, secrets,
generator information or unnecessary payload duplication. Existing domain payloads may
contain their contract-defined business fields because they are the data being
consolidated; this does not authorize additional sensitive metadata.

## Acceptance criteria

- [ ] **AC-01:** A complete exact five-domain chain produces one consolidated record.
- [ ] **AC-02:** Personal + Bank produces one valid incomplete operational component.
- [ ] **AC-03:** Location + Professional + Net produces one valid incomplete
      operational component.
- [ ] **AC-04:** An exact Personal-to-Location bridge connects the remaining
      Professional and/or Net fragments transitively.
- [ ] **AC-05:** Missing domains are represented as `null` without invented data.
- [ ] **AC-06:** Unrelated fragments or components never merge.
- [ ] **AC-07:** Exact mismatches do not match through case, whitespace, diacritic or
      fuzzy normalization.
- [ ] **AC-08:** Only the four ADR-0006 rule identifiers can create correlations.
- [ ] **AC-09:** Ambiguous components are marked `ambiguous`; evidence is neither
      silently merged nor discarded.
- [ ] **AC-10:** Unresolved input is surfaced and remains recoverable.
- [ ] **AC-11:** Correlation traceability records the stable identifiers of rules
      actually applied.
- [ ] **AC-12:** Every contributing fragment retains approved non-sensitive source
      provenance.
- [ ] **AC-13:** Equivalent logical input in different order produces deterministic
      equivalent output.
- [ ] **AC-14:** Caller input mappings and fragments are not mutated.
- [ ] **AC-15:** No PostgreSQL persistence behavior, persistence identity or global
      business identity key is introduced.

## Test strategy

Future HRP-50 tests use minimized synthetic fixtures only and must not inspect or use
educational-generator artifacts.

Required tests:

- complete five-domain exact chain;
- Personal + Bank partial component;
- Location + Professional + Net partial component;
- transitive Personal -> Location -> Professional/Net chain;
- incomplete component with explicit absent domains;
- unrelated components remain separate;
- exact mismatch;
- case, whitespace and diacritic mismatches;
- ambiguous component surfaced with all evidence retained;
- unresolved input surfaced and not discarded;
- applied correlation-rule identifiers;
- source provenance for every contribution;
- deterministic output under input permutations; and
- input immutability.

The following are explicitly outside HRP-50 tests and belong to HRP-51 or Data
Platform: replay policy, duplicate conflict policy, late events, out-of-order
behavior, reconciliation, update precedence, retry/recovery and PostgreSQL upsert
behavior.

## Risks and limitations

- Equal raw values can produce a false operational merge.
- Different or missing values can produce a false split.
- The correlation evidence is bounded and does not prove identity or uniqueness.
- Future data may introduce collisions absent from the observed sample.
- Missing domains make a component incomplete rather than proving different identity.
- Ambiguous contributions cannot be resolved by HRP-50.
- Exact matching is intentionally sensitive to spelling, case and whitespace.
- Current grouped outputs lack source provenance required by ADR-0006.
- This record is not a universal identity record and has no persistence identity
  semantics.

## Accessibility and sustainability applicability

Accessibility is not applicable to this backend transformation specification because
it introduces no user-facing flow.

Sustainability is applicable through a pure, bounded, deterministic transformation
with no new persistence, network transfer, polling or dependency requirement. No
carbon, energy or deployment claim is made.

## Definition of Done

- This specification is human-reviewed and approved.
- The provenance input contract and open decisions are resolved or explicitly
  accepted.
- Implementation matches this specification and remains within the stated scope.
- Unit and relevant contract/integration tests pass.
- Required lint, formatting, typing and specification validation checks pass.
- No educational generator inspection occurs.
- No PostgreSQL or persistence scope is introduced.
- Documentation and traceability are updated with the implementation.
- The PR is human-reviewed and merged.
- Jira moves to Done only after merge and verifiable evidence.

## Traceability

```text
Jira HRP-50
  -> this specification
  -> ADR-0006
  -> HRP-46 / HRP-47 / HRP-48 / HRP-49 / HRP-61
  -> docs/observations/2026-09-02-HRP-50-adr0006-correlation-evidence.md
  -> future transformation code (pending implementation)
  -> future tests (pending implementation)
  -> human-reviewed PR (pending)
  -> Jira closure after merge and evidence (pending)
```

## Open decisions before implementation

No HRP-50-owned contract decisions remain open. The concrete raw-persistence
representation behind the abstract `SourceReference` is delegated to the existing
ingestion/raw-persistence contract and is not selected by HRP-50. The remaining
implementation dependency is to update the five existing grouper implementations to
satisfy their amended provenance-bearing output contracts. Their domain
specifications now define the required impact; their grouping semantics remain
unchanged.

These decisions must not be resolved by inventing a global identity key, copying PII
into traceability metadata or performing a broad refactor.
