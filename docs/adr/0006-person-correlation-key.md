# ADR-0006: Person correlation key for curated storage

## Status

Accepted - provisional and controlled operational correlation strategy. This is
accepted for constructing the project's consolidated records under the documented
limitations; it is not a claim of real-world identity truth or universal uniqueness.

## Context

The curated PostgreSQL model needs a way to associate raw structural variants
(A-E, per `docs/02-data-contract.md`) that plausibly belong to the same person, so
that `employees`, `locations`, `professional_profiles`, `bank_accounts` and
`network_data` can be joined without duplicating a person across tables.

HRP-29's bounded observation identifies `passport`, `fullname` and `address` as
correlation *candidates* only, because their raw names occur in more than one
variant. It explicitly did not compare their values or establish equality,
uniqueness, normalisation, priority or business meaning
(`docs/observations/2026-08-27-HRP-29-kafka.md`). `docs/specs/HRP-25-modelo-datos.md`
therefore proposes a curated schema with no unique or foreign-key constraint that
would encode a correlation rule.

## Decision

The project accepts the following exact raw-equality edges as a provisional,
controlled operational correlation strategy for HRP-50:

1. `Personal.passport == Bank.passport`.
2. `Personal.name + " " + Personal.last_name == Location.fullname`.
3. `Location.fullname == Professional.fullname`.
4. `Location.address == Net.address`.

Correlation uses exact raw values only. It does not apply case normalization,
whitespace trimming or collapsing, diacritic normalization, fuzzy matching or a
fallback key. Correlation may be transitive across the four approved exact edges.

These edges define an operational relationship for this project and dataset. They
do not establish a universally unique natural key, prove real-world identity, or
authorize a global business identifier. A future technical `person_id` may identify
the resulting consolidated record, but its persistence semantics are outside this
ADR.

Ambiguous, unresolved or incomplete correlation cases must not be silently merged or
discarded. The consolidated layer must be able to represent that uncertainty. The
detailed completeness, duplicate, late-arrival, out-of-order and update policies
belong to HRP-50 and HRP-51 as appropriate.

Database uniqueness, primary keys, foreign keys and `ON CONFLICT`/upsert behavior
belong to the Data Platform persistence specifications and are not decided by this
ADR.

## Required evidence before acceptance

The evidence required before acceptance was:

- Kafka observation beyond HRP-29's bounded sample comparing actual values of
  `passport`, `fullname` and/or `address` across variants for the same underlying
  person, obtained through an authorised, in-scope observation task and not by
  reading the educational generator.
- A documented human-reviewed decision on uniqueness and conflict resolution for
  the chosen operational strategy.
- Test evidence addressing silent merges of different people and splits of one
  person into multiple curated records.

The acceptance evidence is recorded below. The strategy remains provisional because
the authorized evidence does not expose real-world identity ground truth.

## Historical consequences of staying `Proposed`

Before this ADR was accepted, `employees`, `locations`, `professional_profiles`,
`bank_accounts` and `network_data` remained linkable only through the foreign keys
described in `docs/specs/HRP-25-modelo-datos.md`, with cardinality left pending.

Before acceptance, no curated upsert could use a business-key `ON CONFLICT` clause.
HRP-25 was not blocked by the proposed status because it documented the boundary
without assuming an answer.

## HRP-43 evidence assessment - 2026-09-01

The authorised observation is recorded in
`docs/observations/2026-09-01-HRP-43-person-correlation.md`. It analysed 2,000 RAW
events from the corrected clean collection using exact raw equality without
normalization or hashing. `passport` supports a partial Personal/Bank connection,
`fullname` supports a partial Location/Professional connection, and `address`
supports a partial Location/Net connection. A subsequent authorized chain audit
also observed the Personal/Location derived-name bridge and 249 five-domain
connected components.

The evidence does not expose true person identity, collision ground truth, universal
coverage, completeness, or conflict semantics. At the time of that investigation,
the global HRP-43 outcome was **Insufficient evidence** and ADR-0006 remained
Proposed and blocked. The subsequent human architecture decision accepts the
controlled operational strategy above despite these limitations; absence of observed
collisions remains not evidence of uniqueness.

HRP-44 and HRP-45 may proceed independently where they do not require global person
identity. Complete person aggregation may proceed under the accepted operational
strategy in HRP-50, while business uniqueness and persistence enforcement remain
governed by the boundaries documented below.

## HRP-46 operational clarification - 2026-09-02

For HRP-46 only, human architectural review authorizes `fullname` as a
domain-local operational correlation key for Location grouping. This is an ETL
processing decision under the limitations above; it is not new empirical evidence
and did not change the ADR's global status at that time.

An exact equal `fullname` places Location fragments in the same operational bucket.
It does not prove that they represent the same real-world person, is not a global
`person_id`, is not a cross-domain key, and does not establish uniqueness. Missing
or unusable values remain uncorrelated. Exact repeated evidence may be handled
idempotently, while distinct values under one operational bucket remain explicit
conflicts and are not silently resolved or discarded.

HRP-46 does not use `address`, `passport`, email, telephone, IBAN, a composite,
fuzzy matching or a fallback key. Its local key does not become a universally
unique business key through this ADR.

## Acceptance evidence and decision evidence

The decision is based on the authorized read-only observation of the corrected RAW
collection `hr_pro.raw_events_hrp43_20260901`, containing 2,000 RAW events. The
evidence is recorded in `docs/observations/2026-09-01-HRP-43-person-correlation.md`
and the subsequent sanitized correlation-chain audit.

Observed exact-equality evidence:

- Personal/Bank: 397 shared candidates; all observed matches were one-to-one.
- Location/Professional: 399 shared candidates; all observed matches were one-to-one.
- Location/Net: 400 shared candidates; all observed matches were one-to-one.
- Personal/Location derived-name bridge: 251 shared candidates; all observed
  matches were one-to-one.
- Transitive graph: 249 observable connected components contained all five domains.
- No one-to-many, many-to-one or many-to-many ambiguity was observed.
- Case, whitespace, diacritic and combined normalization experiments added no
  matches and introduced no observed collisions.

Human architecture review approved this provisional and controlled operational
strategy under the limitations and responsibility boundaries in this ADR. No human
reviewer name, approval timestamp, Jira comment identifier or other unavailable
traceability detail is asserted here.

## Risks and limitations

The accepted strategy retains these explicit risks:

- **False merge:** equal raw values may belong to different real-world people.
- **False split:** different or missing values may belong to the same real-world
  person.
- **Incomplete observation:** a bounded sample may omit domain fragments needed for a
  chain.
- **Future collisions:** later data may introduce collisions absent from the sample.
- **Bounded-sample limitation:** observed one-to-one relationships do not prove
  global uniqueness or identity truth.

HRP-50 transformations must preserve traceability of the contributing source/domain
fragments and the approved correlation rule or rules that connected them. This is an
architectural requirement; the final consolidated-record schema remains owned by
HRP-50.

## Responsibility boundaries

ADR-0006 owns:

- global operational correlation semantics;
- the four approved exact correlation edges;
- normalization policy;
- transitive correlation authorization;
- the identity ambiguity boundary;
- documented limitations and false-merge/false-split risk;
- the architectural traceability requirement.

ADR-0006 does not own:

- the final HRP-50 consolidated-record schema;
- detailed completeness policy;
- duplicate-event handling;
- late/out-of-order handling;
- update semantics;
- PostgreSQL table design;
- primary-key/foreign-key implementation;
- `ON CONFLICT`/upsert implementation.

HRP-50 defines the consolidated-record contract. HRP-51 defines detailed
incomplete, duplicate and out-of-order resilience semantics. Data Platform
specifications define persistence enforcement.

## Acceptance gate

The status is `Accepted` for the provisional and controlled operational strategy
recorded above, based on the authorized evidence and human architecture approval.
Future changes to the approved edges, comparison policy, transitivity, identity
boundary or responsibility boundaries require a new reviewed ADR decision.
