# HRP-43 — Empirical person-correlation discovery

**Status:** Investigation complete; global outcome insufficient evidence; pending human review
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
- The authorised 2026-09-01 observation is recorded in
  `docs/observations/2026-09-01-HRP-43-person-correlation.md`.

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
The authorised observation used the clean collection `raw_events_hrp43_20260901` in
database `hr_pro`, with 2,000 RAW events and zero invalid events. Its evidence record
is linked below. This establishes the dataset used for this investigation; it does
not establish a universal person key or prove person identity.

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
| `passport` | 798 present; 401 distinct; 397 repeated and cross-shape values | Supported as partial Personal/Bank candidate; not universal |
| `fullname` | 801 present; 402 distinct; 399 repeated and cross-shape values | Supported as partial Location/Professional candidate; not universal |
| `address` | 801 present; 401 distinct; 400 repeated and cross-shape values | Supported as partial Location/Net candidate; not universal |
| Composite | No identity-grounded evidence for a universal composite | Insufficient evidence |

Each candidate must end as exactly one of: **Supported by current evidence**,
**Rejected**, or **Insufficient evidence**. No absence of collisions in a small sample
may be presented as proof of uniqueness.

## Evidence record

The resulting sanitised observation is stored at
`docs/observations/2026-09-01-HRP-43-person-correlation.md`. It records method,
authorization, sample scope, provenance policy, field inventory, candidate metrics,
limitations, and reviewer status. It contains no complete payloads or identifying
values.

## Dependencies and downstream implications

HRP-34 is a prerequisite for an authorised RAW observation and has now supplied the
clean dataset used by this investigation. HRP-44 may define
structural classification independently, provided it does not encode person identity;
HRP-45 may define validation/cleaning independently where it does not assume a person
key. Person aggregation, correlation-based curated upserts, and business uniqueness
remain blocked because this evidence does not establish global person identity or
uniqueness. PostgreSQL schema design may proceed without a business-key constraint,
as established by HRP-25.

## Test implications

Future approved correlation logic must cover same-person matches, non-colliding
different-person fragments, missing/null/empty/malformed candidate values, duplicate
events, out-of-order fragments, partial information, conflicts, reprocessing, and any
approved normalization. Tests must not encode an unapproved key and must use synthetic
or properly sanitised authorised evidence. Existing harness cases H-05 and H-06 remain
applicable.

## Acceptance criteria

- [x] Authorised corrected clean RAW source and observation authorization are evidenced;
      human review remains pending.
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
if evidence is insufficient for a defensible decision. The observation is complete for
the authorised sample, but the global correlation outcome remains **Insufficient
evidence** because person identity, collision ground truth, and universal coverage
were not observable.

## Completion evidence

- Specification: this document; investigation complete, pending human review.
- Sanitised observation: `docs/observations/2026-09-01-HRP-43-person-correlation.md`.
- ADR-0006 decision: remains Proposed; pending evidence and separate human review.
- Branch / PR / commit / Jira closure: not authorised in this step.
