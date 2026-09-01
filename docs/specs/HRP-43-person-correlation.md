# HRP-43 — Empirical person-correlation discovery

**Status:** Draft; blocked pending authorised clean RAW evidence and human review
**Owner:** Gabriela
**Jira:** HRP-43
**Branch:** `investigation/HRP-43-person-correlation`
**Dependencies:** Reviewed HRP-34 clean RAW boundary; authorised MongoDB RAW observation
**Related ADR:** `docs/adr/0006-person-correlation-key.md`

## Objective

Determine, from authorised empirical evidence, whether an observed field, combination
of fields, or other observable mechanism can reliably associate fragments belonging to
the same person. This specification does not select or implement a person key.

## Source of truth and confirmed facts

- `docs/01-architecture.md` places correlation downstream of MongoDB RAW persistence.
- `docs/02-data-contract.md` and `docs/observations/2026-08-27-HRP-29-kafka.md`
  record five neutral structural variants from a bounded sample of 20 JSON objects.
- `passport`, `fullname`, and `address` are candidates only because their names occur
  in more than one observed variant. No candidate values were compared.
- `topic + partition + offset` is technical event identity/idempotency provenance,
  never person identity.
- `docs/adr/0006-person-correlation-key.md` remains Proposed and blocked pending
  cross-variant value evidence and decisions on uniqueness, conflicts, completeness,
  normalization, and enforcement.
- HRP-34 documents clean configurable targets via `MONGODB_COLLECTION` and
  `MONGODB_INVALID_COLLECTION`; its legacy collection is not an authorised HRP-43
  source.

## Scope

### Includes

- A reproducible observation protocol for authorised RAW events.
- Candidate coverage, missing/null/empty values, repeated values, collisions,
  cross-variant matching, representation differences, and counterexamples.
- Composite candidates only where observed evidence justifies evaluating them.
- Technical provenance, privacy-safe evidence recording, and explicit limitations.
- Evidence requirements for supporting, rejecting, or leaving a candidate unresolved.
- Downstream implications and future test requirements.

### Excludes

- Inspecting or using the educational data generator.
- Production correlation, person aggregation, or curated upserts.
- Changing Kafka-to-MongoDB ingestion or the HRP-34 raw boundary.
- Inventing normalization, conflict, completeness, or uniqueness rules.
- PostgreSQL business-key constraints or `ON CONFLICT` correlation logic.
- HRP-44 classification and HRP-45 validation/cleaning implementation.
- Changing ADR-0006 status, Jira, or another team member’s scope.

## Authorised RAW source gate

The configured collection mechanism is documented by HRP-34, but a configuration
variable alone does not prove that a particular collection exists, was produced by
the corrected ingestion path, or is authorised as value-level evidence for HRP-43.
The repository currently provides no value-level RAW observation, collection
inventory, or evidence identifying a specific clean dataset as an authorised HRP-43
source. Empirical observation therefore remains blocked until that source is
established.

Before observation, a human-reviewed procedure must identify the clean collection,
confirm that it was produced by the corrected ingestion path, record its
authorisation for HRP-43 observation, and exclude the legacy/incompatible
collection. No data source may be inferred from generator code or from an
undocumented collection name.

## Permitted and prohibited evidence

Permitted evidence is repository documentation, approved specifications and ADRs,
Kafka messages actually consumed through an authorised procedure, corrected MongoDB
RAW documents, and sanitised observation records derived from those sources.

Do not inspect generator source, retain complete payloads, expose personal/banking
values, or place raw values in tracked documentation, logs, screenshots, commits, or
test output. Record counts, equality/mismatch relationships, masked examples where
safe, and technical provenance. Follow existing project redaction guidance; do not
invent a new hashing policy.

## Observation protocol

1. Obtain a defined, authorised sample from the corrected clean RAW collection.
2. Record sample scope and each event’s `topic`, `partition`, `offset`, and
   `received_at` where safe, without retaining unnecessary payload values.
3. Identify observed field sets and types without assigning business semantics.
4. For each candidate, compare actual raw values across event shapes; retain only
   privacy-safe equality, mismatch, and count results.
5. Measure presence/coverage, missing/null/empty values, distinctness, repeated
   values, cross-shape matches, collisions, and representation differences.
6. Search deliberately for counterexamples: same value with conflicting identity
   evidence, different values for otherwise evidenced same-person fragments, and
   ambiguous or incomplete groups.
7. Evaluate composites only after individual evidence and an explicit rationale.
8. Repeat on an independent sample where feasible and record sample limitations.
9. Separate observed facts, inferences, hypotheses, and decisions in the evidence.

No normalization may hide raw differences. If a normalization hypothesis is tested,
report raw and transformed comparisons separately and leave approval pending.

## Candidate evaluation and decision states

| Candidate | Evidence required | Current status |
|---|---|---|
| `passport` | Cross-variant value matches, coverage, collisions and counterexamples | Insufficient evidence |
| `fullname` | Cross-variant value matches, coverage, collisions and counterexamples | Insufficient evidence |
| `address` | Cross-variant value matches, coverage, collisions and counterexamples | Insufficient evidence |
| Composite | Evidence-backed component rationale and collision analysis | Insufficient evidence |

Each candidate must end as exactly one of: **Supported by current evidence**,
**Rejected**, or **Insufficient evidence**. No absence of collisions in a small sample
may be presented as proof of uniqueness.

## Evidence record

The resulting sanitised observation should be stored under `docs/observations/` with
the observation date and HRP-43 reference. It must state method, authorization,
sample scope, provenance policy, field inventory, candidate matrix, missingness,
matches, collisions, counterexamples, limitations, and reviewer status. It must not
contain complete payloads or identifying values.

## Dependencies and downstream implications

HRP-34 is a prerequisite for an authorised RAW observation. HRP-44 may define
structural classification independently, provided it does not encode person identity;
HRP-45 may define validation/cleaning independently where it does not assume a person
key. Person aggregation, correlation-based curated upserts, and business uniqueness
remain blocked until HRP-43 evidence and ADR-0006 approval exist. PostgreSQL schema
design may proceed without a business-key constraint, as established by HRP-25.

## Test implications

Future approved correlation logic must cover same-person matches, non-colliding
different-person fragments, missing/null/empty/malformed candidate values, duplicate
events, out-of-order fragments, partial information, conflicts, reprocessing, and any
approved normalization. Tests must not encode an unapproved key and must use synthetic
or properly sanitised authorised evidence. Existing harness cases H-05 and H-06 remain
applicable.

## Acceptance criteria

- [ ] Authorised corrected clean RAW source and human review status are evidenced.
- [ ] No generator material, complete payload, secret, or identifying value is used.
- [ ] Protocol preserves safe technical provenance and separates facts from inference.
- [ ] Candidate coverage, missingness, repetition, collisions, representation
      differences, cross-variant matches, and counterexamples are reported when data
      exists; unavailable metrics remain explicitly pending.
- [ ] Candidate outcomes use only the three permitted decision states.
- [ ] Technical Kafka identity is not used as person identity.
- [ ] No production correlation, business uniqueness, normalization, or ADR acceptance
      is introduced by this task.
- [ ] Observation evidence receives human review before any downstream implementation.

## Stop conditions and current blockers

Stop if the source would require generator inspection, if documentation materially
contradicts the authorised boundary, if the clean RAW source cannot be authorised, or
if evidence is insufficient for a defensible decision. Current empirical observation
is blocked because no specific clean RAW dataset has yet been evidenced as an
authorised HRP-43 value-level source satisfying the HRP-34 clean-data boundary.

## Completion evidence

- Specification: this document; pending human review.
- Sanitised observation: pending authorised evidence acquisition.
- ADR-0006 decision: remains Proposed; pending evidence and separate human review.
- Branch / PR / commit / Jira closure: not authorised in this step.
