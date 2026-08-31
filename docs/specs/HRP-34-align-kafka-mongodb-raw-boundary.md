# HRP-34 — Align Kafka-to-MongoDB raw persistence boundary

**Status:** Ready for implementation
**Owner:** Gabriela
**Owner approval:** Gabriela, 2026-08-31
**Human PR reviewer:** Miguel — pending
**Jira:** HRP-34
**Baseline:** `develop` at `58b6bbcea47eb459c80ea78467c7533570aa3f6c`
**Dependencies:** HRP-29 observation, HRP-24 contract, HRP-25 raw model, and the
HRP-30/HRP-31 consumer
**Operational context, not a dependency:** HRP-53 and the shared development Compose
**Related ADR:** `docs/adr/0002-raw-and-curated-storage.md`,
`docs/adr/0003-evidence-first-data-contract.md`, and
`docs/adr/0005-kafka-acknowledgement-after-raw-persistence.md` (`Proposed`)
**Planned branch:** `fix/HRP-34-align-raw-persistence`

## Objective

Align the Kafka-to-MongoDB boundary so that every Kafka record reaches a durable,
idempotent raw-storage outcome before its offset may advance.

The corrected path preserves the actual Kafka topic, partition, offset, receipt time
and original technical value without classification, normalisation or business
validation. It must provide reproducible evidence that a MongoDB failure cannot
silently advance an affected Kafka topic-partition.

## Context and scope

### Includes

- Restore `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_CONSUMER_GROUP` and `KAFKA_TOPICS` as
  validated environment-driven configuration.
- Introduce typed Kafka coordinates, raw envelopes and per-coordinate persistence
  results.
- Persist every parseable JSON object in `raw_events` before structural
  classification, including `unknown` and `non-conforming` objects.
- Preserve the actual Kafka topic, partition and offset.
- Use `payload` and `processing_status = "pending"`, aligned with the approved raw
  model.
- Route missing values, invalid UTF-8, non-parseable JSON and JSON non-objects to
  `invalid_events`.
- Store the exact approved `invalid_events` envelope: actual Kafka coordinates, UTC
  receipt time, `payload`, closed technical `reason` and
  `processing_status = "invalid"`.
- Preserve `payload` as BSON Binary only when original bytes exist. Store
  `payload: null` when `msg.value()` is actually `None`; never fabricate `b""`.
- Keep BSON evidence exclusively inside MongoDB; it must never appear in logs,
  documentation or test output.
- Treat a durable `invalid_events` insert or verified duplicate as sufficient raw
  evidence for Kafka acknowledgement.
- Implement idempotency using a unique compound index on actual
  `topic + partition + offset`.
- Return the exact coordinates that were inserted or already existed.
- Return `unresolved_conflict` and withhold acknowledgement when the same coordinates
  already exist in the opposite durable collection.
- Commit only the highest contiguous durable offset per topic-partition.
- Emit technical-only logs without payloads, personal values, failed MongoDB
  operations or exception text that may embed them.
- Add AC-linked unit, contract and real-MongoDB integration tests.
- Use simulated Kafka messages with real MongoDB for the reproducible integration
  boundary in this task.
- Update README, runbook, model, observability and ADR evidence with the implemented
  behaviour in the future implementation PR.
- After merge, document the verified impact in HRP-34, HRP-35, HRP-36 and HRP-37
  without automatically changing their Jira states.

### Excludes

- HRP-43 correlation, comparison or person aggregation.
- HRP-44 classification or mapping of observed variants to business categories.
- HRP-45 business validation, cleaning or normalisation.
- Treating `detector.py` or `validator.py` as approved rules. They remain physically
  present but must be removed from the Ingestion execution path.
- Business duplicate detection, payload hashing or deduplication using personal
  fields.
- Redis, PostgreSQL application integration, SQL, API, frontend or Prometheus
  deployment.
- A broker-backed automated E2E test. A real Kafka-broker execution remains a manual
  or later approved decision.
- Reading, cloning, searching, inspecting or analysing the educational data
  generator.
- Deleting, mutating or migrating the existing MongoDB collection.
- Inferring the original Kafka topic of pre-alignment documents.
- Declaring HRP-34, HRP-35, HRP-36 or HRP-37 corrected or changing their Jira states.
- Accepting ADR-0005 before Miguel reviews the implementation and evidence.

### Verified facts

- The current consumer classifies and validates before persistence.
- The current MongoDB document stores an inferred category as `topic`.
- The current writer returns one boolean for a whole batch.
- The current consumer may commit discarded records before raw persistence.
- HRP-29 observed a bounded single-partition sample; multi-partition behaviour is a
  required technical test, not an observed data fact.
- `unknown` and `non-conforming` are not equivalent to invalid.
- ADR-0005 remains `Proposed`.
- HRP-22 narrative documents describe initial raw persistence as completed while also
  recording that the final raw envelope still requires alignment. Those narrative
  claims do not replace the repository completion gates, this specification or
  ADR-0005 evidence.
- HRP-53 added PostgreSQL to the shared `infra/compose.dev.yml` without modifying the
  MongoDB service.

### Approved human decisions

- Gabriela owns this correction and approved this specification for implementation
  planning on 2026-08-31.
- Miguel is the human PR reviewer; his final review remains pending.
- A durable `invalid_events` outcome permits Kafka acknowledgement.
- Parseable JSON objects always enter `raw_events`, including unknown and
  non-conforming structures.
- The initial technical status is `pending`.
- Missing, invalid UTF-8, non-parseable and JSON non-object values enter
  `invalid_events`.
- Technically invalid original bytes are retained as BSON Binary exclusively in
  MongoDB. A genuinely missing Kafka value is stored as `payload: null`; `b""` is not
  an authorised substitute.
- `invalid_events.reason` is one of `missing_value`, `invalid_utf8`, `invalid_json`
  or `non_object_json`, and its `processing_status` is exactly `invalid`.
- The corrected load uses a clean collection selected through configuration.
- The existing collection is preserved unchanged and its original Kafka topics are
  not inferred.
- MongoDB is mandatory for integration tests; Kafka messages may be simulated.
- A real-broker E2E is not claimed by this task.
- Offset advancement is calculated independently per topic-partition and only across
  the contiguous durable prefix.

### Risks

- The current MongoDB collection uses an incompatible envelope and cannot be assumed
  repairable because the original Kafka topic was not retained.
- `infra/compose.dev.yml` is shared with PostgreSQL. Local HRP-34 tests must start only
  `mongo` and must not use teardown commands that stop PostgreSQL or delete shared
  volumes. A full Compose teardown is permitted only in an isolated CI job that owns
  the entire Compose project.
- Changing commit behaviour can reduce throughput if commits are synchronous or too
  frequent.
- Unordered MongoDB bulk writes can partially succeed; result mapping must not report
  failed or unknown coordinates as durable.
- `raw_events` and `invalid_events` have collection-local indexes. Routing must remain
  deterministic across retries, restarts and compatible versions, and an opposite-
  collection coordinate collision must never create a second durable outcome.
- Logging driver error details may expose the failed MongoDB operation.
- Simulated Kafka messages plus real MongoDB prove the controlled adapter boundary,
  not behaviour against a real broker.
- HRP-22 status wording may cause HRP-43 to consume pre-alignment data prematurely.
  HRP-43 remains blocked for observation until a corrected clean collection exists.

## Design

### Raw boundary

The Ingestion worker performs only the technical work required to preserve evidence:

1. Read Kafka transport metadata.
2. Decode UTF-8 and parse JSON.
3. Route a JSON object to `raw_events`, regardless of its structural conformance.
4. Route an approved technical failure to `invalid_events`.
5. Persist the outcome durably.
6. Return the exact durable coordinates.
7. Advance only safe per-topic-partition offsets.

No A–E label, business category, correlation, cleaning or semantic validation occurs
before durable persistence.

### `raw_events` envelope

A raw document contains only the approved evidence boundary:

- `payload`: decoded JSON object with keys and values unchanged;
- `topic`: actual Kafka topic;
- `partition`: Kafka partition;
- `offset`: Kafka offset;
- `received_at`: UTC receipt time;
- `processing_status`: technical state, initially `pending`.

It does not contain an inferred category or a `valid` business/structural flag.

### `invalid_events` envelope

`invalid_events` is reserved for technical failures:

- missing Kafka value;
- invalid UTF-8;
- non-parseable JSON;
- parseable JSON whose top-level value is not an object.

It contains exactly the following approved fields:

| Field | Type / value | Meaning |
|---|---|---|
| `topic` | string | Actual Kafka topic |
| `partition` | integer | Actual Kafka partition |
| `offset` | integer | Actual Kafka offset |
| `received_at` | UTC datetime | Platform receipt time |
| `payload` | BSON Binary or `null` | Original bytes when present; `null` only when `msg.value()` is `None` |
| `reason` | closed technical string | `missing_value`, `invalid_utf8`, `invalid_json` or `non_object_json` |
| `processing_status` | string | Exact value `invalid` |

The implementation must not manufacture `b""` or any other byte sequence for a
missing value. Empty bytes received from Kafka are original bytes and are distinct
from `None`.

The original value is storage evidence only. It is prohibited from logs, exception
messages, test output, PR evidence and documentation.

A structurally unknown or non-conforming JSON object is not routed here; it remains a
raw event for downstream processing. Routing depends only on the immutable Kafka
value and follows this closed order:

1. `value is None` -> `invalid_events` with `missing_value` and `payload: null`;
2. invalid UTF-8 -> `invalid_events` with `invalid_utf8` and BSON Binary payload;
3. non-parseable JSON -> `invalid_events` with `invalid_json` and BSON Binary payload;
4. valid JSON whose top level is not an object -> `invalid_events` with
   `non_object_json` and BSON Binary payload;
5. any JSON object -> `raw_events`, including unknown and non-conforming objects.

This decision must remain stable across retries, restarts and compatible versions.

### Typed boundaries

Production boundaries use typed objects rather than leaking untyped tuples or
dictionaries. The planned responsibilities are equivalent to:

- Kafka coordinates: topic, partition and offset;
- raw/invalid envelope: coordinates, evidence value, receipt time and technical
  status/reason;
- persistence outcome: coordinate plus `inserted`, `already_exists`, `failed` or
  `unresolved_conflict`.

Exact Python class names are implementation details, but one boolean for an entire
batch is not sufficient.

### Idempotency

- Use actual Kafka `topic + partition + offset` as the only raw identity.
- Apply a unique compound index to each collection that durably receives Kafka
  records.
- Do not use inferred categories, payload hashes or business fields.
- A duplicate-key result for the same coordinates is a durable idempotent outcome.
- A non-duplicate write error is unresolved and does not authorise a commit.
- An unknown driver or write-concern result is unresolved. Redelivery plus the unique
  index provides safe recovery.
- The writer reports the status of every input coordinate, including partial bulk
  outcomes.
- Before inserting, the persistence boundary must detect whether the same coordinates
  already exist in the opposite collection. If they do, it must not insert a second
  document, must return `unresolved_conflict`, must leave that offset uncommitted and
  must require human review.
- An `unresolved_conflict` log contains only topic, partition, offset and technical
  error type. It contains neither payload nor the failed or existing MongoDB
  operation.

### Per-topic-partition commit strategy

For every consumed batch:

1. Persist each record outcome and receive a result per Kafka coordinate.
2. Group consumed records and results by actual topic and partition.
3. Order each topic-partition's records by offset.
4. Starting at its first consumed offset, find the highest contiguous prefix whose
   records are durably inserted or already present in `raw_events` or
   `invalid_events`.
5. Stop at the first failed or unresolved coordinate for that topic-partition.
6. Commit Kafka's next offset, `highest_durable_offset + 1`, for that partition.
7. Allow unrelated topic-partitions to advance independently.
8. Use an explicit synchronous commit or inspect every returned partition result.
9. Treat a Kafka commit failure as safe redelivery; it never deletes or rolls back
   MongoDB evidence.
10. Never commit a later offset across a failed gap.

### Configuration and clean-data boundary

- Values come from the process environment or local `.env`, with process environment
  taking precedence.
- Required blank values fail startup validation.
- Topics are parsed from the authorised comma-separated environment value.
- Broker, group, topics, database and collection are not hard-coded.
- `MONGODB_COLLECTION` remains the canonical configuration variable for selecting
  the `raw_events` target. `MONGODB_INVALID_COLLECTION` follows the same project
  convention for selecting `invalid_events`.
- The corrected run selects clean raw and invalid collections by changing those
  configuration values, not by renaming, modifying, deleting or migrating an existing
  collection.
- The existing collection remains unchanged and is not an authorised HRP-43 source.
- HRP-43 remains blocked for observation until the corrected collection and its
  integration evidence have received human review.

### Shared Compose operation

- Local integration starts only the MongoDB service:

  `docker compose -f infra/compose.dev.yml up -d mongo`

- Local cleanup must not run a project-wide teardown that would stop PostgreSQL or
  remove shared volumes. It must target MongoDB or use an isolated Compose project.
- An isolated CI job may perform a full teardown only when it owns every service and
  volume in that Compose project.

### Logging and security

Logs may contain topic, partition, offset, technical status, error type, counts and
timing. They must not contain:

- raw or invalid values;
- Kafka keys;
- exception text that may embed message bytes;
- MongoDB `writeErrors` operations;
- connection strings, credentials or private endpoints;
- personal, banking or correlation values.

## Acceptance criteria

- [ ] AC-01: Kafka broker, consumer group and topics are loaded from validated
      environment configuration and are not hard-coded.
- [ ] AC-02: Every parseable JSON object is offered to raw persistence before any
      classifier or business validator is invoked.
- [ ] AC-03: Unknown and non-conforming JSON objects are persisted in `raw_events`
      without an inferred category.
- [ ] AC-04: `raw_events` preserves `payload`, actual Kafka topic, partition, offset,
      UTC receipt time and `processing_status = "pending"`.
- [ ] AC-05: Every technical-invalid case produces the exact approved
      `invalid_events` envelope and reason code. Original bytes use BSON Binary;
      `msg.value() is None` uses `payload: null`; no absent value is represented by
      fabricated bytes.
- [ ] AC-06: Replaying the same actual topic-partition-offset produces one durable
      outcome across both collections and no business/content deduplication. A
      coordinate found in the opposite collection returns `unresolved_conflict`,
      creates no second document and requires human review.
- [ ] AC-07: The persistence adapter returns the exact inserted, already-existing and
      failed or `unresolved_conflict` Kafka coordinates, including partial-batch
      outcomes.
- [ ] AC-08: A successful insert or verified duplicate in either durable collection
      permits only the affected topic-partition's contiguous offset to advance.
- [ ] AC-09: A MongoDB timeout, connection error, write-concern error or non-duplicate
      failure, including `unresolved_conflict`, does not advance across the affected
      coordinate.
- [ ] AC-10: A multi-partition batch advances each topic-partition independently and
      never crosses a failed gap; the committed value is the last contiguous durable
      offset plus one.
- [ ] AC-11: Logs and test output contain technical metadata and error types but no
      payload, invalid BSON value, personal value, failed MongoDB operation, secret or
      endpoint.
- [ ] AC-12: `detector.py` and `validator.py` remain outside the Ingestion path and no
      HRP-44/HRP-45 rule is approved by this change.
- [ ] AC-13: Unit, contract and real-MongoDB integration tests cover success,
      duplicate, technical-invalid input, partial failure, multi-partition commit and
      restart/redelivery.
- [ ] AC-14: Local integration starts only `mongo` and its cleanup neither stops
      PostgreSQL nor deletes shared volumes; full teardown is limited to an isolated
      CI-owned Compose project.
- [ ] AC-15: README, raw model, observability guidance and runbook match the
      implemented behaviour without presenting a real-broker E2E unless one was
      actually executed.
- [ ] AC-16: Existing incompatible data remains unchanged and is not silently treated
      as the authorised HRP-43 source; the corrected load uses a clean configured
      collection selected with `MONGODB_COLLECTION` and
      `MONGODB_INVALID_COLLECTION`.
- [ ] AC-17: Specification validation, pre-commit, Ruff, formatting, mypy, pytest,
      coverage and Compose validation pass in CI.
- [ ] AC-18: Miguel reviews the ingestion/storage boundary and records whether
      ADR-0005 has enough evidence to move from `Proposed` to `Accepted`.
- [ ] AC-19: Before merge, draft HRP-34, HRP-35, HRP-36 and HRP-37 Jira comments exist
      with explicit evidence placeholders and no completion claim. Publishing comments
      populated with real evidence is a post-merge follow-up, not a pre-merge PR gate.
- [ ] AC-20: Accessibility is documented as not applicable and sustainability
      evidence covers bounded batching, idempotency and avoidance of unbounded
      redelivery without energy or carbon claims.

## Accessibility and sustainability applicability

- Accessibility: not applicable. This task introduces no user-facing flow, API
  response, rendered interface or interactive control.
- Sustainability: applicable to processing efficiency. The implementation keeps
  batches bounded, avoids duplicate storage, prevents uncontrolled acknowledgement
  across failures and avoids indiscriminate service teardown. Evidence consists of
  deterministic duplicate, failure, batching and recovery tests, not an energy or
  carbon claim.
- Deferred claims: no WCAG conformance, energy saving, carbon result, production
  throughput or deployment claim is authorised by this task.

## Test strategy

| Level | Case | Provenance | Owner | Observable evidence |
|---|---|---|---|---|
| Unit | Valid environment settings, comma-separated topics and blank required values | `synthetic` | HRP-34 implementer | Valid settings load; each blank required value rejects startup |
| Unit | Raw object reaches persistence before any processing rule | `synthetic` | HRP-34 implementer | Persistence spy is called with unchanged object and actual coordinates; detector/validator spies are not called |
| Unit | Five-way deterministic routing | `synthetic` | HRP-34 implementer | `None`, invalid UTF-8, invalid JSON, non-object JSON and object each reach the specified collection and reason |
| Unit | Invalid envelope and missing value | `synthetic` | HRP-34 implementer | Bytes remain bytes; `None` produces `payload: null`; no path manufactures `b""` |
| Unit | Partial bulk result, unknown write concern and opposite-collection conflict | `synthetic` | HRP-34 implementer | Every coordinate receives a result; unknown/conflict coordinates are unresolved and omitted from commit |
| Unit | Contiguous offsets across several topic-partitions | `synthetic` | HRP-34 implementer | Each partition advances independently to its highest contiguous durable offset plus one and stops at its first gap |
| Contract | Exact raw and invalid envelopes | `synthetic` | HRP-34 implementer | Field names, types, four reason codes and exact statuses match this specification |
| Integration | BSON Binary and missing value in real MongoDB | `synthetic` | HRP-34 implementer | Non-parseable bytes read back as BSON Binary; a missing Kafka value reads back as `payload: null` |
| Integration | Real MongoDB unique indexes, replay and opposite-collection conflict | `synthetic` | HRP-34 implementer | Replay leaves one document; opposite-collection collision leaves counts unchanged and returns `unresolved_conflict` |
| Integration | Real MongoDB partial and failure paths | `synthetic` | HRP-34 implementer | Returned coordinates distinguish durable, failed, unknown and conflict outcomes without leaking operations |
| Integration | Simulated Kafka messages plus real MongoDB | `synthetic` | HRP-34 implementer | Captured commits contain only next offsets for each contiguous durable topic-partition prefix |
| Integration | Clean configured collections and legacy preservation | `synthetic` | HRP-34 implementer | Writes target configured clean raw/invalid collections; before/after evidence shows the prior collection is unchanged |
| Recovery | Re-run after persistence but before Kafka commit | `synthetic` | HRP-34 implementer | Redelivery is reported as already existing and permits the same safe next offset |
| Operational | Start and stop only MongoDB in the shared Compose | `synthetic` | HRP-34 implementer | PostgreSQL state is unchanged and no MongoDB or PostgreSQL shared volume is removed |
| Documentary | Align README, raw model, observability and runbook | N/A | HRP-34 implementer; Miguel reviews | Documentary diff describes only implemented and executed behaviour |
| Documentary | Accessibility and sustainability applicability | N/A | HRP-34 implementer; Miguel reviews | Accessibility remains not applicable; bounded batching/idempotency evidence is cited without energy or carbon claims |
| Manual/E2E | Real Kafka broker | `sanitised-observed` if later authorised | Human operator | Explicitly pending unless separately executed; no broker result is claimed by this PR |
| Security | Capture failure-path logs and test output | `synthetic` | HRP-34 implementer; Miguel reviews | No payload, BSON value, PII, URI, secret or MongoDB operation appears |
| Quality | Full repository harness and Compose syntax | N/A | CI; Miguel reviews | Every configured command exits successfully and the 75% coverage floor is met |
| Human review | Ingestion/storage boundary, CODEOWNERS and ADR-0005 | N/A | Miguel plus required CODEOWNERS reviewers | Required approvals are recorded; ADR-0005 remains `Proposed` until Miguel's explicit decision |

## Validation and operational evidence

The implementation PR must record exact commands and results for:

- specification validation;
- pre-commit, Ruff, format and mypy;
- pytest with the configured 75% coverage floor;
- Compose syntax validation;
- real-MongoDB integration;
- clean collection selection by configuration;
- BSON Binary/null persistence and all four invalid reason codes;
- opposite-collection `unresolved_conflict` without offset acknowledgement;
- verification that PostgreSQL remained unaffected by local integration cleanup;
- documentary alignment and accessibility/sustainability review;
- GitHub quality, governance and label checks.

Narrative HRP-22 completion claims are context only. They are not substitutes for
these results, Miguel's review or the repository completion gate.

## Rollback and recovery

- Revert the future implementation PR if the corrected worker cannot consume safely.
- Do not delete MongoDB or PostgreSQL volumes as part of rollback.
- Do not reset Kafka offsets without explicit human approval.
- Preserve the legacy collection unchanged until the team decides its disposition.
- Recover a failed Kafka commit after successful MongoDB persistence through
  redelivery and the unique technical index.

## Closing evidence

- Planning approval: Gabriela, 2026-08-31.
- Branch: `fix/HRP-34-align-raw-persistence`.
- Implementation PR: pending.
- Commits: pending.
- Validation results: pending.
- Real-MongoDB integration evidence: pending.
- Clean collection evidence: pending.
- Miguel review: pending.
- ADR-0005 decision: remains `Proposed` pending Miguel's review.
- HRP-34/35/36/37 impact comments: pending until merge.
- Pre-merge Jira comment drafts with placeholders: pending.
- Post-merge publication with real evidence: follow-up, not a PR acceptance gate.
- Jira status changes: not authorised by this specification.
