# HRP-24 — Define the observed Kafka data contract

**Status:** Draft; documentary implementation authorised
**Owner:** Gaby
**Human reviewer:** Anahí
**Jira:** HRP-24
**Dependencies:** HRP-29 completed; its reviewed evidence is available on `develop`
**Related ADR:** `docs/adr/0003-evidence-first-data-contract.md`
**Planned branch:** `feature/HRP-24-contrato-datos`

## Objective

Define the minimum structural data contract supported by the approved HRP-29
observation. The contract must allow provisional technical conformance
classification without inventing business categories, canonical names, field
semantics, correlation rules, ordering guarantees or person aggregation rules.

## Recorded evidence

The authorised source is
`docs/observations/2026-08-27-HRP-29-kafka.md`, produced by HRP-29, reviewed by the
team and merged into `develop`. It records a bounded structural observation of 20
JSON objects from topic `probando`, partition `0`, with five distinct top-level field
sets. No message values or complete payloads were retained in the evidence document.

The public project documentation remains published context. It is not evidence that
an observed structure has a particular business meaning.

## Context and scope

### Includes

- The raw field names and apparent types observed by HRP-29.
- Neutral technical labels A–E for the five observed structures.
- Provisional structural conformance classification against those structures.
- An explicit `non-conforming/unknown` outcome relative to the observed contract.
- The evidence boundaries for correlation, ordering, duplication and completeness.
- Unknowns and decisions that require further evidence and human approval.

### Excludes

- Mapping A–E to Personal, Location, Professional, Bank or Net Data.
- Canonical field names, raw-field normalisation or semantic equivalences.
- Business validation of field values or interpretation of `sex`, `salary` or any
  other value.
- A definitive correlation key, conflict resolution or person aggregation.
- Business duplicate detection, business ordering or completeness rules.
- Treating `probando` as a universal or fixed system topic.
- A classifier, ETL implementation, executable schema, fixtures or additional tests.

## Contract design

### Evidence levels

The contract uses three evidence levels:

| Level | Meaning |
|---|---|
| Observed | Structure recorded in the approved, bounded HRP-29 observation. |
| Published/provisional | Context from authorised public documentation, not proof of the observed payload or its meaning. |
| Unknown/pending | A rule or meaning not demonstrated by HRP-29 and requiring further evidence or human decision. |

An observed fact is limited to the recorded sample. It is not proof that the five
variants are exhaustive or stable for future messages.

### Observed Kafka scope

HRP-29 observed topic `probando`, partition `0`, and 20 valid JSON objects. This is
the scope of the recorded sample only. The topic name is not a universal system
configuration, and the sample does not establish guarantees for other topics,
partitions, sessions or future structures.

### Observed structural variants

A–E are neutral technical labels and have no approved business-domain mapping.

| Variant | Count in sample | Exact raw fields | Apparent/observed types |
|---|---:|---|---|
| A | 7 | `IPv4`, `address` | Both fields: string |
| B | 4 | `company`, `company address`, `company_email`, `company_telfnumber`, `fullname`, `job` | All fields: string |
| C | 4 | `IBAN`, `passport`, `salary` | All fields: string |
| D | 3 | `address`, `city`, `fullname` | All fields: string |
| E | 2 | `email`, `last_name`, `name`, `passport`, `sex`, `telfnumber` | `sex`: array; all other fields: string |

Raw field names are preserved exactly as observed. Apparent types describe JSON
structure only. They do not establish formats, domains, ranges or business meaning.
The contents and meaning of the observed `sex` array were not assessed.

Every field was absent from at least one other variant. No JSON `null` was observed
while a listed field was present. These facts do not establish whether any field is
required, optional or nullable; those properties remain unknown.

### Provisional conformance classification

An object may receive provisional technical label A, B, C, D or E only when its
top-level field set and apparent JSON types match the corresponding observed
structure exactly.

This classification is relative to the bounded HRP-29 evidence. It is not a business
taxonomy, a canonical schema, a guarantee about future structures or proof that the
message belongs to a particular person or business domain.

### Non-conforming/unknown outcome

An object is `non-conforming/unknown` relative to this observed contract when it has
additional fields, missing fields, different apparent types or JSON `null` where
HRP-29 did not observe it. Such an object must not be forced into A–E and must not be
used to infer new semantics.

`Non-conforming/unknown` does not automatically mean business-invalid. The definitive
downstream treatment remains a pending decision where it is not already established
by the approved architecture.

### Correlation and aggregation boundary

`passport`, `fullname` and `address` are correlation candidates only because their
raw names occur in more than one observed variant. HRP-29 did not compare their
values or establish equality, uniqueness, normalisation, priority or business
meaning.

This contract does not define a correlation key, conflict-resolution rule, completed
person condition or person aggregation rule. It does not authorise joining variants
or writing a curated person from them.

### Ordering and duplication boundary

HRP-29 establishes no cross-variant, cross-partition or business ordering guarantee
and no completed-person sequence.

No repeated topic/partition/offset appeared in the sample. Business duplicates and
incomplete person groups were not assessed. Existing raw-event technical idempotency
is a separate architecture decision and does not constitute business duplicate
detection.

### Security considerations

- Do not add complete payloads, real values, PII, banking data, secrets or private
  broker details to the contract, fixtures, logs or review evidence.
- Do not read, inspect, search, infer from or otherwise use the educational data
  generator.
- Treat field names and structural types as the maximum evidence available from
  HRP-29; do not reconstruct values or generator behaviour.

## Acceptance criteria

- [ ] HRP-29 is recorded as a completed dependency and its approved observation is
      the source for every observed structural claim.
- [ ] A–E reproduce only the exact raw field names and apparent types recorded by
      HRP-29 and remain neutral technical labels.
- [ ] Exact field-set and apparent-type matching produces only provisional technical
      conformance classification, with no claim of exhaustiveness or future stability.
- [ ] The contract contains no mapping between A–E and Personal, Location,
      Professional, Bank or Net Data.
- [ ] Additional or missing fields, different types and unobserved JSON `null` produce
      `non-conforming/unknown`, without automatically declaring the data
      business-invalid.
- [ ] Required, optional and nullable properties remain unknown where HRP-29 did not
      demonstrate them.
- [ ] Raw field names remain unchanged, and apparent types do not create semantic or
      format validation rules.
- [ ] `passport`, `fullname` and `address` are correlation candidates only; no
      definitive correlation key, person grouping or conflict resolution is defined.
- [ ] HRP-29 creates no ordering or completeness guarantee, and the absence of
      repeated Kafka coordinates creates no business duplicate rule.
- [ ] `probando` is documented only as the observed topic and not as universal system
      configuration.
- [ ] Unknowns and pending decisions remain explicit and no complete payload, real
      value, PII, secret or generator material is included.
- [ ] `docs/02-data-contract.md` is aligned with this specification and the applicable
      documentary quality checks pass.

## Validation strategy

HRP-24 is a documentary contract task. It does not add runtime behaviour or an
executable schema, so no new classifier, ETL, fixture or pytest coverage is required.

| Level | Case | Expected evidence |
|---|---|---|
| Documentary | Compare A–E with HRP-29 | Exact raw fields, counts and apparent types match the observation. |
| Traceability | Review evidence levels and claims | Observed, published/provisional and unknown content remain distinct. |
| Boundary review | Inspect classification, correlation and ordering rules | No business mapping, definitive correlation, person grouping or ordering guarantee. |
| Security review | Inspect the spec and contract | No payload values, PII, secrets or generator material. |
| Quality | Run the repository spec validator and applicable pre-commit hooks | Commands pass without unrelated changes. |
| Human review | Review the documentary diff | Anahí records approval before HRP-24 is closed. |

## Unknowns and pending decisions

- Whether or how A–E relate to the published business information groups.
- Field semantics, formats, domains, ranges and canonical naming.
- Required, optional and nullable properties.
- The meaning and allowed contents of `sex`, `salary` and every other value.
- Contract evolution and versioning when new structures are observed.
- The definitive correlation key and any normalisation, uniqueness or conflict rules.
- Person completeness and aggregation rules.
- Ordering across variants, partitions or business records.
- Business duplicate detection.
- Definitive downstream treatment of `non-conforming/unknown` structures.
- Operational topic configuration beyond the bounded `probando` observation.

## Completion evidence

- Branch / PR: pending.
- Commit: pending.
- Updated contract: pending.
- Validation commands and results: pending.
- Human reviewer approval: pending.
- Jira closing comment: pending; closure is not authorised by this draft.
