# HRP-51 — Handle incomplete, duplicate and out-of-order information

**Status:** Implemented and merged; documentation evidence update pending before Jira closure
**Owner:** Gabriela Granja
**Human reviewer:** Miguel
**Jira:** HRP-51
**Planned branch:** `feature/HRP-51-handle-incomplete-duplicate-order`
**Implementation branch:** `feature/HRP-51-reconciliation-tests`
**Dependencies:** HRP-50 consolidated person record; HRP-96 consolidation contract hardening (merged via [PR #44](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/44)); HRP-46, HRP-47, HRP-48, HRP-49 and HRP-61 domain groupers; approved source-provenance contract
**Related ADR:** [`docs/adr/0006-person-correlation-key.md`](../adr/0006-person-correlation-key.md)

## Objective

Define the transformation-level behavior for recomputing consolidated operational
records when known domain fragments are incomplete, repeated, conflicting or received
in a different order. The behavior must preserve evidence, provenance and uncertainty
without inventing recency or identity semantics.

This specification does not claim that operational correlation proves real-world
identity.

## Context and scope

Included:

- deterministic recomputation from the currently known logical fragment set;
- order-independent consolidation;
- transitions caused by additional valid evidence;
- explicit duplicate, conflict, ambiguity and unresolved outcomes;
- transformation-level idempotency and provenance preservation;
- focused synthetic behavior tests.

Excluded:

- changes to HRP-50's consolidated-record shape or base statuses;
- changes to ADR-0006 correlation edges, normalization or transitivity;
- PostgreSQL schema, primary keys, foreign keys, upserts or persistence idempotency;
- Kafka acknowledgement, retry, consumer offset or redelivery policy;
- API, frontend, generator behavior or new RAW/Kafka discovery;
- last-write-wins, first-write-wins or any timestamp/offset recency rule.

The current repository baseline contains the merged HRP-50 implementation and the
HRP-96 consolidation-contract hardening on `develop`. HRP-51 treats both as upstream
contracts and does not redefine them. The branch is based on that current baseline.

## Dependencies and source of truth

- [`docs/01-architecture.md`](../01-architecture.md) defines the transformation
  boundary and separates raw, temporary and curated responsibilities.
- [`docs/02-data-contract.md`](../02-data-contract.md) records that ordering,
  business duplicates, completeness and conflict rules are not established by the
  observed contract.
- [`docs/specs/HRP-50-consolidated-person-record.md`](HRP-50-consolidated-person-record.md)
  defines the consolidated result, `complete`/`incomplete`/`ambiguous` statuses and
  the exclusion of detailed replay and late-arrival behavior.
- HRP-46/47/48/49/61 define domain-local exact-key grouping, exact evidence
  deduplication and ambiguity preservation.
- ADR-0006 defines the four approved exact operational correlation edges.

No educational-generator artifact or new RAW/Kafka observation is required or
authorized.

## Input contract

HRP-51 consumes the existing grouped domain results for Personal, Location,
Professional, Bank and Net, including their grouped fragments, unresolved material
and abstract `SourceReference` values.

Unresolved input uses the shared transformation-level `UnresolvedFragment` contract
from `transformation/fragment_contract.py`: `status`, original `payload`, upstream
`classification`, `source_reference` and technical `reason`. HRP-51 preserves this
contract when carrying unresolved material into the HRP-50
`UnresolvedContribution` boundary; it does not define a parallel unresolved type.

The four ADR-0006 edges remain the only permitted cross-domain correlations:

| Rule identifier | Exact relationship |
|---|---|
| `personal_bank_passport` | `Personal.passport == Bank.passport` |
| `personal_location_fullname` | `Personal.name + " " + Personal.last_name == Location.fullname` |
| `location_professional_fullname` | `Location.fullname == Professional.fullname` |
| `location_net_address` | `Location.address == Net.address` |

Comparison remains exact raw equality. No trimming, case folding, diacritic
normalization, fuzzy matching, composite fallback or inferred key is allowed.

## Output contract

The output remains `ConsolidationResult` as defined by HRP-50 and hardened by HRP-96:

- consolidated records with the five explicit domain contributions;
- each domain contribution retains its original `DomainGroupContribution` entries,
  including each local group `key` and its `GroupedFragment` values;
- `complete`, `incomplete` or `ambiguous` status;
- applied correlation-rule identifiers;
- canonical source provenance;
- unresolved contributions represented separately and recoverably.

HRP-51 adds no persistence identifier, global `person_id`, database field or API
shape. A recomputation replaces the transformation result for the supplied logical
fragment set; persistence of that result is outside this task. Same-domain group
boundaries must not be flattened in a way that loses the distinction between local
groups.

## Transformation behavior

The conceptual flow is:

```text
currently known fragments
    -> apply existing domain grouping and approved exact correlations
    -> deterministic recomputation
    -> consolidated records + unresolved material
```

Recomputation must be pure with respect to caller-owned inputs. Equivalent logical
fragment sets must produce equivalent records, evidence, statuses, rules and
provenance regardless of arrival or iteration order.

Additional valid fragments received after an earlier computation may trigger another
computation. This describes recomputation only; it does not establish event-time
lateness.

## Incomplete-data behavior

HRP-50 remains authoritative for the `incomplete` status: a correlatable,
unambiguous component with one or more absent domains is incomplete, and absent
domains remain explicit `null` values.

The following conceptual transitions are supported:

- `incomplete -> complete` when valid additional evidence supplies all missing
  domains without ambiguity;
- `incomplete -> ambiguous` when additional evidence introduces a same-domain
  conflict or otherwise prevents one unambiguous contribution.

Unresolved material may become part of a later result only after it is supplied again
in a form accepted by the existing validation, classification and grouping contracts.
No hidden mutable state or inferred correction is introduced.

`ambiguous -> complete` is not defined. It requires an explicit correction,
retraction or approved conflict-resolution contract.

## Duplicate and replay behavior

These concepts remain distinct:

1. The same source event replayed.
2. The same payload with the same `SourceReference`.
3. The same payload with a different `SourceReference`.
4. The same domain-local key with a different payload.
5. Kafka redelivery.

The existing groupers deduplicate the same payload plus the same source reference.
They retain the same payload with a different source reference as separate
`GroupedFragment` instances; when those fragments share a local grouping key, the
local group is `ambiguous`. This existing behavior is accepted by HRP-51 and must
remain deterministic and provenance-preserving.

The following remain open decisions and are not silently converted into requirements:

- whether `SourceReference` is guaranteed unique and stable enough to identify an
  exact replay;
- whether equal payloads with different source references represent one business
  event or distinct source events remains unresolved at the semantic/business level;
- whether replay identity is owned by transformation or by raw ingestion.

Kafka redelivery and raw-event idempotency remain ingestion responsibilities.

## Different-order behavior

The result for the same logical fragment set must not depend on:

- arrival order;
- Python dictionary/set iteration order;
- MongoDB insertion order;
- Kafka offset order.

Groups, fragments, unresolved entries, rules and provenance must use the established
canonical deterministic ordering. Order independence is not recency semantics.

## Conflict and ambiguity behavior

Different payloads under the same approved domain-local grouping key remain explicit
evidence and produce an ambiguous outcome. No payload is silently selected, merged or
discarded.

The repository supplies no approved event time, source-system version, business
version or recency field. Therefore HRP-51 defines no precedence between conflicting
values. Last-write-wins, first-write-wins, highest-offset-wins and timestamp-wins are
prohibited unless a future reviewed contract authorizes one.

## Provenance requirements

Every retained grouped fragment must preserve its abstract, non-sensitive
`SourceReference` through recomputation. Provenance must be stable and canonically
ordered, and must not embed complete raw events, secrets, PII-derived hashes or
generator information.

`SourceReference` may support provenance, deterministic ordering and audit lookup. It
may support exact replay detection only if the upstream contract guarantees stable
uniqueness. It is not event time, chronology, version or recency.

## Determinism and idempotency expectations

For AC-01, AC-02 and AC-05, a “same logical fragment set” means equality of the
exact `(payload, SourceReference)` pairs. Payload values are not normalized, and a
different source reference makes a distinct transformation input even when the
payload is byte-for-byte/equivalently represented. The existing groupers therefore
retain such fragments separately and mark a shared local group `ambiguous`.

The transformation is idempotent in the following limited sense:

- recomputing the same logical fragment set yields the same result;
- repeating the same payload with the same source reference does not multiply output;
- equivalent input permutations yield equivalent output.

The transformation behavior for equal payloads with different source references is
defined by AC-06: they are distinct transformation inputs, remain separate
`GroupedFragment` evidence and a shared local grouping key is `ambiguous`. The
business interpretation of those differing
references remains open: HRP-51 does not determine whether they represent the same
underlying business fact, independent observations, corrections, retransmissions or
another business relationship. Persistence idempotency and Kafka delivery semantics
remain outside this specification.

## Error and unresolved behavior

Malformed, unsupported, non-correlatable or contract-inconsistent material remains in
the existing explicit unresolved representation with its available context,
reference and technical reason. It must not be silently dropped or fabricated into a
consolidated record.

Transformation errors must remain isolated according to the existing worker error
policy. Retry and acknowledgement behavior are owned by ingestion/platform
contracts.

## Acceptance criteria

- [ ] **AC-01:** Recomputing an unchanged logical fragment set, defined as the same
      exact `(payload, SourceReference)` pairs, produces the same records, statuses,
      evidence, rules, provenance and unresolved material.
- [ ] **AC-02:** Equivalent logical input, defined by the same exact
      `(payload, SourceReference)` pairs, in different arrival orders produces an
      equivalent result.
- [ ] **AC-03:** An incomplete unambiguous component becomes complete when valid
      additional domain evidence supplies every missing domain.
- [ ] **AC-04:** Additional conflicting same-domain evidence preserves all distinct
      evidence and changes the result to `ambiguous`.
- [ ] **AC-05:** Repeating the same exact `(payload, SourceReference)` pair does not
      multiply consolidated fragments.
- [ ] **AC-06:** Equal payloads with different source references are retained as
      separate `GroupedFragment` evidence; when they share a local grouping key, the
      group is `ambiguous`, with no evidence discarded.
- [ ] **AC-07:** No arrival order, Kafka offset, insertion order or unapproved
      timestamp is used as business recency.
- [ ] **AC-08:** No conflicting value is silently selected, merged or discarded.
- [ ] **AC-09:** Every retained contribution preserves its approved source reference.
- [ ] **AC-10:** Unresolved material remains explicitly represented and recoverable.
- [ ] **AC-11:** No normalization, fallback correlation, global identity key,
      persistence behavior, API behavior or ingestion acknowledgement behavior is
      introduced.

Tests requiring a business interpretation of equal payloads with different source
references, or a replay identity guarantee beyond the exact pair behavior, remain
blocked until the open contract questions below are decided.

## Test scenarios

| Scenario | Expected evidence | Readiness |
|---|---|---|
| Same payload and same source reference repeated | One retained contribution; deterministic result | Ready |
| Same logical input in two arrival orders | Equal transformation results | Ready |
| Incomplete component receives missing valid domain | `incomplete -> complete` | Ready |
| Incomplete component receives conflicting same-domain evidence | `incomplete -> ambiguous`; all evidence retained | Ready |
| Same domain-local key with different payloads | Explicit ambiguity; no winner | Ready |
| Equal payload with different source references | Separate `GroupedFragment` values; shared local key is `ambiguous`; provenance retained | Ready |
| Unresolved material supplied again in correlatable form | Appears in later recomputation | Requires explicit reprocessing test contract |
| Provenance survives recomputation | Stable references retained and canonically ordered | Ready after source contract confirmation |
| Ambiguous component becomes complete | No transition without correction/retraction policy | Negative test; policy required |
| Kafka redelivery and acknowledgement | No HRP-51 assertion | Owned by ingestion |

Tests use minimized synthetic fixtures only. No educational-generator artifact,
complete raw payload or new RAW/Kafka observation may be used.

## Implementation evidence

HRP-51 reuses the existing deterministic transformation path and introduces no new
reconciliation layer. The implementation uses:

- the Personal, Location, Professional, Bank and Net groupers;
- `GroupedFragment` and the shared `UnresolvedFragment` contract;
- `DomainGroupContribution` boundaries in `ConsolidatedPersonRecord`; and
- `consolidate_person_records(...)` as the production entry point.

No production-code change was required because the existing groupers and consolidator
already satisfy the approved HRP-51 behavior.

Implementation and executable acceptance evidence were delivered in PR #47. The
acceptance-evidence strengthening was recorded in commit `2cd5d43`. PR #47 was merged
into `develop` by merge commit `f175fd9`.

The delivered evidence records:

- focused HRP-51 tests: 9 passed;
- full suite: 147 passed, 5 skipped;
- total coverage: 87.57%, above the required 75% minimum;
- GitHub CI: 3/3 checks passed;
- Ruff: passed;
- Ruff format: passed;
- mypy: passed;
- pre-commit: passed; and
- specification validation: passed for 30 files.

AC-03 explicitly verifies one complete consolidated record, all five non-null domain
contributions, preservation of the original Personal and Bank evidence, and the five
expected source references. AC-10 explicitly verifies one unresolved contribution,
the original synthetic payload, source reference, context and the exact
`classification_mismatch` reason.

The business interpretation of equal payloads with different `SourceReference` values
remains intentionally open; the transformation behavior remains the defined
AC-06 behavior and is not changed by this evidence record.

## Observability and traceability

Transformation metrics/logs may count recomputations, unresolved outcomes,
ambiguous outcomes and duplicate evidence without logging sensitive payloads. The
implementation must retain the applied correlation-rule identifiers and source
references required by HRP-50.

Operational delivery evidence must identify the specification, focused tests, type
and lint validation, while preserving the raw/temporary/curated boundaries.

## Open decisions and unresolved contract questions

1. Does the upstream/raw contract guarantee that `SourceReference` is stable and
   unique per source event?
2. Are equal payloads with different source references one business event or
   distinct source events? The transformation behavior is fixed as separate evidence
   and ambiguity; only this business interpretation remains open.
3. Is exact replay detection a transformation responsibility or an ingestion/raw
   responsibility?
4. Is there any approved business/version timestamp for conflict precedence? Current
   permitted evidence provides none.
5. Is “late arrival” merely post-recomputation arrival, or is a time-based meaning
   required? No lateness window, watermark or event-time rule may be assumed.
6. What explicit correction/retraction mechanism, if any, can resolve an ambiguous
   component?

Until resolved, conflicting values remain ambiguous and no recency rule exists.

## ADR assessment

No new ADR is required for deterministic recomputation, order independence, local
duplicate handling or ambiguity preservation when these remain within the existing
transformation boundary.

A new ADR would be required before adopting a durable cross-cutting policy for replay
identity, recency/version precedence, event-time lateness or ownership of mutable
correlation state. This task does not create such an ADR.

## Accessibility and sustainability applicability

- Accessibility: not applicable — this is a backend transformation specification
  with no user-facing flow.
- Sustainability: applicable through bounded deterministic recomputation, no new
  dependency, no polling and no additional persistence or network transfer in this
  specification. No measured efficiency claim is made.
- Deferred claims: no accessibility conformance, carbon, energy or deployment claim
  is made.

## Definition of Done

- Open decisions are resolved or explicitly accepted by human review.
- Implemented behavior and executable acceptance evidence match this specification
  without expanding into persistence, ingestion, API or frontend scope.
- Focused duplicate, order, incomplete, conflict, unresolved and provenance tests
  pass using synthetic fixtures.
- Relevant lint, formatting, typing and specification validation checks pass.
- `git diff --check` passes.
- No educational-generator inspection or new RAW/Kafka discovery occurs.
- Implementation documentation and traceability are updated after the merged work.
- This evidence update is merged before HRP-51 is closed in Jira; Jira closure must
  reference the merged implementation and documentation evidence.

## Implemented impact

The implementation changed no production code. Existing HRP-50, domain groupers,
PostgreSQL, Kafka ingestion, APIs and infrastructure boundaries remain unchanged.
No additional production implementation artifact was required; executable HRP-51
acceptance evidence is provided by the focused test suite delivered through PR #47.

## Traceability

```text
Jira HRP-51
  -> this specification
  -> HRP-50 consolidated-record contract
  -> HRP-46/47/48/49/61 domain grouping contracts
  -> ADR-0006 operational correlation boundary
  -> focused behavior tests
  -> PR #47 implementation/evidence delivery
  -> acceptance-evidence commit `2cd5d43`
  -> merge commit `f175fd9`
  -> this final specification evidence update
  -> Jira closure after merged documentation and evidence
```
