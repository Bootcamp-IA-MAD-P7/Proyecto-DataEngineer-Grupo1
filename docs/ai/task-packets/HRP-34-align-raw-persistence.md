# Task packet — HRP-34

**Status:** Implementation complete; pending human review
**Owner:** Gabriela
**Owner approval:** Gabriela, 2026-08-31
**Human PR reviewer:** Miguel — pending
**Jira:** HRP-34
**Spec:** `docs/specs/HRP-34-align-kafka-mongodb-raw-boundary.md`
**Baseline:** `develop` at `58b6bbcea47eb459c80ea78467c7533570aa3f6c`
**Planned branch:** `fix/HRP-34-align-raw-persistence`

## Expected outcome

A reviewed Kafka-to-MongoDB boundary in which every Kafka record receives a durable,
idempotent raw-storage outcome before its topic-partition offset may advance.

The corrected MongoDB source preserves actual Kafka coordinates and an opaque decoded
JSON object without classification, business validation or normalisation. Technical
invalid bytes are retained only as BSON Binary inside `invalid_events`; a truly absent
Kafka value is retained as `payload: null`, never fabricated bytes. Reproducible
failure-path evidence must exist before the corrected clean collection may be used by
HRP-43.

## Authorised context

- Briefing / task: HRP-34 correction approved by Gabriela on 2026-08-31.
- Repository baseline: `58b6bbcea47eb459c80ea78467c7533570aa3f6c`.
- Core instructions and standards:
  - `AGENTS.md`
  - `CONTRIBUTING.md`
  - `docs/base-standards.md`
  - `docs/documentation-standards.md`
  - `docs/backend-standards.md`
  - `docs/04-sdd-workflow.md`
- Architecture, contract and model:
  - `docs/01-architecture.md`
  - `docs/02-data-contract.md`
  - `docs/03-data-model.md`
  - `docs/observations/2026-08-27-HRP-29-kafka.md`
  - `docs/specs/HRP-24-observed-data-contract.md`
  - `docs/specs/HRP-25-modelo-datos.md`
  - `docs/specs/HRP-30-kafka-consumer.md`
  - `docs/specs/HRP-31-continuous-ingestion.md`
- Decisions and harness:
  - `docs/adr/0002-raw-and-curated-storage.md`
  - `docs/adr/0003-evidence-first-data-contract.md`
  - `docs/adr/0005-kafka-acknowledgement-after-raw-persistence.md`
  - `docs/05-test-harness.md`
  - `docs/06-observability.md`
- Current operational and narrative context:
  - `docs/07-runbook.md`
  - `infra/compose.dev.yml`
  - `docs/specs/HRP-53-postgres-docker.md`
  - `docs/dailies/2026-08-31-global-closeout.md`
  - `docs/presentation-sources/evidence/2026-08-31-ingestion-storage-and-quality.md`
  - `README.md`
- AI governance:
  - `docs/ai/human-approval-policy.md`
  - `docs/ai/evaluation-rubric.md`
  - `ai-specs/agents/ingestion-engineer.md`
  - `ai-specs/skills/enrich-us/SKILL.md`
  - `ai-specs/skills/spec-driven-task/SKILL.md`
  - `ai-specs/skills/code-auditing/SKILL.md`

The HRP-29 observation is bounded structural evidence only. It does not establish
business categories, multi-partition behaviour or a universal topic. HRP-22 narrative
completion statements are context and do not replace the completion gate, the HRP-34
specification, tests or human review.

## Approved decisions

- Gabriela owns the correction; Miguel reviews the future PR.
- The correction is traced primarily to HRP-34 and records impact in HRP-35, HRP-36
  and HRP-37 only after merge.
- Durable `invalid_events` persistence permits Kafka acknowledgement.
- Every parseable JSON object enters `raw_events`, including unknown and
  non-conforming structures.
- Unknown does not mean invalid.
- Initial technical state is `processing_status = "pending"`.
- Missing values, invalid UTF-8, non-parseable JSON and JSON non-objects enter
  `invalid_events`.
- `invalid_events` contains actual `topic`, `partition`, `offset`, UTC `received_at`,
  `payload`, `reason` and `processing_status = "invalid"`.
- `payload` is BSON Binary when original bytes exist and `null` only when
  `msg.value()` is actually `None`; manufacturing `b""` for absence is prohibited.
- `reason` is exactly one of `missing_value`, `invalid_utf8`, `invalid_json` or
  `non_object_json`.
- BSON evidence remains exclusively in MongoDB and never appears in logs,
  documentation or test output.
- The legacy collection remains unchanged and is not migrated.
- Corrected loading uses a clean collection selected through configuration.
- Original Kafka topics are not inferred from legacy documents.
- `detector.py` and `validator.py` remain in the repository but outside the Ingestion
  path; this task does not approve or implement HRP-44 or HRP-45.
- MongoDB real is mandatory for integration; simulated Kafka messages are approved.
- A real Kafka-broker E2E remains manual or subject to a later decision.
- ADR-0005 remains `Proposed` until Miguel reviews the technical evidence.
- Offsets are calculated and committed independently per topic-partition over only
  the contiguous durable prefix.
- Routing depends only on the immutable Kafka value and remains stable across retries,
  restarts and compatible versions: `None`, invalid UTF-8, invalid JSON and non-object
  JSON enter `invalid_events`; every JSON object enters `raw_events`.
- If coordinates already exist in the opposite collection, no second document is
  inserted: the result is `unresolved_conflict`, the offset remains uncommitted, logs
  contain only coordinates and technical error type, and human review is required.
- `MONGODB_COLLECTION` selects the raw target and
  `MONGODB_INVALID_COLLECTION` selects the invalid target using the existing project
  naming convention. Clean targets are selected through configuration only.
- CODEOWNERS requirements must be checked before the future PR.

## Dependencies and limits

- Depends on: reviewed HRP-29/24/25 evidence, the HRP-30/31 consumer boundary and a
  real local/CI MongoDB service.
- Operational context, not dependency: HRP-53 added PostgreSQL to the shared
  development Compose without changing the MongoDB service.
- Does not include: HRP-43 correlation, HRP-44 classification, HRP-45 validation,
  Redis, PostgreSQL application integration, API, frontend or business semantics.
- Does not authorise: reading the educational generator; using detector/validator as
  approved rules; deleting/migrating legacy data; changing Jira; accepting ADR-0005;
  merging or closing work without human review.
- HRP-43 remains blocked for observation until a corrected clean MongoDB collection
  and its evidence have been reviewed.
- Risk: the shared Compose now also contains PostgreSQL. Local HRP-34 integration
  starts only `mongo` and must not use teardown that stops PostgreSQL or deletes
  shared volumes. Full teardown is allowed only in an isolated CI job that owns the
  whole Compose project.
- Risk: simulated Kafka messages plus real MongoDB do not prove a real-broker E2E.
- Risk: HRP-22 narrative status can be misread as completion evidence even though the
  raw boundary remains unaligned.
- Risk: collection-local unique indexes do not by themselves prevent the same
  coordinate from existing in both collections; deterministic routing and the
  `unresolved_conflict` path are mandatory.
- Restriction: do not read, clone, search, inspect or analyse the educational data
  generator.

## Request to the assistant

**Role:** `ingestion-engineer`, using `enrich-us`, `spec-driven-task` and
`code-auditing`.

**Concrete question:** Implement only the approved HRP-34 correction so that raw
persistence precedes processing and offsets advance independently per
topic-partition only across the exact contiguous set of durable Kafka coordinates.

**Expected output format:**

1. small, typed production changes;
2. AC-linked unit, contract and real-MongoDB integration tests;
3. documentation updated with actual behaviour;
4. exact commands and results;
5. evidence that PostgreSQL and shared volumes were not affected by local tests;
6. self-audit findings;
7. English PR description;
8. pre-merge Jira impact-comment drafts containing explicit evidence placeholders.

Publishing those comments with real evidence is a post-merge follow-up and is not a
pre-merge acceptance gate.

**Required test evidence:**

- Real MongoDB reads back original non-parseable bytes as BSON Binary.
- Real MongoDB reads back `payload: null` when `msg.value()` is `None`.
- Each of the four closed `reason` codes is asserted explicitly.
- Coordinates found in the opposite collection return `unresolved_conflict`, create
  no document and produce no Kafka commit for that offset.
- `MONGODB_COLLECTION` and `MONGODB_INVALID_COLLECTION` select clean targets through
  configuration.
- Before/after checks prove that the prior collection is neither written, modified nor
  deleted.
- Every technical fixture is minimised, contains no real value and is labelled
  `synthetic`; any later broker-derived fixture must be minimised, sanitised and
  labelled `sanitised-observed`.

**Evaluation criteria:**

- no invented Kafka or business facts;
- actual Kafka topic preserved;
- no pre-persistence classification or business validation;
- deterministic raw/invalid routing;
- original invalid values isolated as BSON Binary in MongoDB;
- missing Kafka values stored as `payload: null`, never fabricated bytes;
- all four closed reason codes verified explicitly;
- per-coordinate persistence results;
- opposite-collection conflicts return `unresolved_conflict` and prevent commit;
- safe contiguous per-topic-partition commit calculation;
- no payload, BSON evidence or PII in logs and test output;
- real MongoDB integration evidence;
- clean configured targets with before/after proof that the prior collection is
  unchanged;
- technical fixtures labelled `synthetic`, minimised and free of real values;
- no disruption to the shared PostgreSQL service or volumes;
- no HRP-43/44/45 implementation;
- ADR-0005 remains Proposed until Miguel's decision;
- Miguel performs the human review.

## Human review of the result

- [ ] Facts and assumptions are separated.
- [ ] Cited paths and references exist.
- [ ] No Kafka field, topic or behaviour is invented.
- [ ] The raw/curated boundary is preserved.
- [ ] Unknown and invalid outcomes are not conflated.
- [ ] The exact `invalid_events` fields, BSON/null rule, four reason codes and
      `processing_status = "invalid"` are implemented and tested.
- [ ] Actual Kafka coordinates drive idempotency.
- [ ] Opposite-collection coordinate conflicts create no second document, return
      `unresolved_conflict` and do not commit.
- [ ] Per-topic-partition commits have no off-by-one or gap error.
- [ ] Logs contain no payload, BSON evidence, personal value or failed MongoDB
      operation.
- [ ] Existing data is unchanged and is not declared authoritative.
- [ ] The corrected load uses a clean configured collection.
- [ ] `MONGODB_COLLECTION` and `MONGODB_INVALID_COLLECTION` select the clean targets,
      and before/after evidence proves the prior collection is unchanged.
- [ ] Local integration starts only MongoDB and does not stop PostgreSQL or delete
      shared volumes.
- [ ] Tests and CI evidence are reproducible.
- [ ] A real-broker E2E is not claimed without execution evidence.
- [ ] README and operational documentation match the implemented state.
- [ ] CODEOWNERS and required reviewers were checked.
- [ ] Miguel remains the designated reviewer and every additional mandatory
      CODEOWNER review is satisfied.
- [ ] ADR-0005 status changes only after Miguel's explicit review.
- [ ] HRP-34/35/36/37 are not declared corrected without post-merge evidence.
- [ ] Pre-merge Jira comment drafts contain placeholders; publication is left to the
      authorised post-merge follow-up.
- [ ] The result has been applied or rejected with a recorded reason.

## AI usage log

- Tool / role: Codex; ingestion-engineer; enrich-us; spec-driven-task;
  code-auditing.
- Date: 2026-08-31.
- Planning output: evidence-based specification and task packet for the
  Kafka-to-MongoDB raw-boundary correction, updated for baseline `58b6bbc`, HRP-22
  narrative drift and the HRP-53 shared Compose context.
- Human planning decision: approved by Gabriela for implementation preparation on
  2026-08-31.
- Technical result: not implemented.
- Miguel review: pending.
- Additional mandatory CODEOWNERS reviewers: pending determination before PR.
- ADR-0005 decision: remains `Proposed`.
