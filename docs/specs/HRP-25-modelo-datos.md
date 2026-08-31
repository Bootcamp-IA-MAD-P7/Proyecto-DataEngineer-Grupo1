# HRP-25 — Design the MongoDB and PostgreSQL data model

**Status:** Draft; documentary implementation authorised
**Owner:** Johans
**Human reviewer:** Gaby
**Jira:** HRP-25
**Dependencies:** HRP-24 completed; its reviewed contract is available on `develop`
**Related ADR:** `docs/adr/0002-raw-and-curated-storage.md`, `docs/adr/0003-evidence-first-data-contract.md`
**Planned branch:** `feature/HRP-25-modelo-datos`

## Objective

Produce a documented, human-reviewable proposal for the MongoDB raw model and the
PostgreSQL curated model, so that future implementation tasks (raw persistence,
ETL → PostgreSQL, table creation) can start from an approved design instead of an
implicit one. This task designs; it does not implement.

## Context and scope

### Includes

- Minimum-viable MongoDB collection design (`raw_events`, `invalid_events`,
  `processing_audit`), building on the outline already present in
  `docs/03-data-model.md`.
- Proposed PostgreSQL curated tables (`employees`, `locations`,
  `professional_profiles`, `bank_accounts`, `network_data`, `processing_audit`):
  candidate columns, types, primary/foreign keys, indexes and idempotency
  constraints, with every unconfirmed item marked as such.
- An explicit statement of the boundary between what MongoDB stores (raw evidence)
  and what PostgreSQL stores (curated, queryable records).
- A list of which design decisions require an ADR versus a spec-only note.
- An update to `docs/03-data-model.md` reflecting this proposal.

### Excludes

- SQL, migrations, Docker, ETL code, API code or any executable artifact.
- A definitive correlation key, person-aggregation rule or conflict-resolution rule:
  HRP-24 does not provide one.
- A mapping between structural variants A–E and the published business groups
  (Personal, Location, Professional, Bank, Net Data).
- Invented field names, types, canonical naming, `required`/`nullable` rules or
  business semantics not evidenced by HRP-24/HRP-29.
- Any reading, cloning or inspection of the educational data generator.

### Verifiable assumptions

- HRP-24's observed contract (`docs/02-data-contract.md`,
  `docs/specs/HRP-24-observed-data-contract.md`) is the only source of structural
  facts used in this design; the public README is treated as provisional context
  only, per ADR-0003.
- `docs/specs/HRP-24-observed-data-contract.md` still lists its own completion
  evidence as "pending" even though its PR (#12, commit `3085244`) is merged into
  `develop`. This spec treats the merged documentary content as the source of truth
  and flags the stale status line as a documentation inconsistency for HRP-24's
  owner (Gaby) to correct, rather than treating it as a blocker for HRP-25.
- No new Kafka observation has been performed for HRP-25; no field, type or rule
  absent from HRP-24 is introduced here.

### Risks

- A future correlation-key decision may require re-normalising the PostgreSQL design
  proposed here (e.g. additional unique constraints, a new linking table).
- Treating `non-conforming/unknown` structures as out of scope for curated storage
  may need revisiting once a downstream treatment is approved.
- This design is not validated against real message volume or duplicate patterns
  beyond the bounded HRP-29 sample.

## Design

### Zone boundary: MongoDB raw vs. PostgreSQL curated

| Aspect | MongoDB (raw) | PostgreSQL (curated) |
|---|---|---|
| Content | Original payload, unrenamed and unnormalised | Fields resolved to structurally classified, business-approved data only |
| Identity | `topic + partition + offset` (technical, per ADR-0002/architecture invariants) | Table-level primary keys, to be defined once a correlation rule exists |
| Classification | Technical processing status only (`pending`, `processed`, `invalid`, …) | None recorded here beyond what is already curated |
| Written by | `ingest-worker` | `process-worker`, after classification and any approved business rule |
| Source of truth for | Auditable evidence, reprocessing | Business queries via API/dashboard |
| Never contains | A resolved "person" record, a correlation decision, a business classification | A raw/unclassified payload, PII beyond what is explicitly approved for curated storage |

This boundary is a direct application of ADR-0002 and the architecture invariants in
`docs/01-architecture.md` ("Redis no puede ser necesaria para reconstruir la verdad
de negocio", "un evento raw conserva payload original y metadatos Kafka"). No new
invariant is introduced.

### MongoDB: raw zone

Collections (unchanged from `docs/03-data-model.md`, restated with field-level detail):

#### `raw_events`

| Field | Type | Purpose | Evidence status |
|---|---|---|---|
| `payload` | JSON object | Original evidence, unrenamed, unnormalised | Required by ADR-0002; content is opaque per ADR-0003 |
| `topic` | string | Kafka technical metadata | Observed (HRP-29: `probando`) |
| `partition` | integer | Kafka technical metadata | Observed (HRP-29: partition `0`) |
| `offset` | integer | Kafka technical metadata | Observed (HRP-29: strictly increasing in sample) |
| `received_at` | datetime (UTC) | Platform receipt time | Architecture requirement, not Kafka-observed |
| `processing_status` | technical string enum | Operational state, not a business classification | Architecture requirement; exact enum values are `pending` |

Proposed unique index: compound `(topic, partition, offset)`, matching the
idempotency invariant in `docs/01-architecture.md`. Whether this index is enforced
before or after Kafka acknowledgement is governed by ADR-0005, which remains
`Proposed` pending HRP-34; this spec does not change that status.

Structural classification (A–E or `non-conforming/unknown` per
`docs/02-data-contract.md`) is **not** stored as a field on `raw_events` in this
proposal — it is a runtime classification performed by `process-worker`, not a
persisted raw fact, so recording it here would blur the raw/curated boundary.
Whether and where to persist that classification for audit purposes is `pending`.

#### `invalid_events`

| Field | Type | Purpose |
|---|---|---|
| `payload` | JSON object (or raw bytes, if not parseable) | Evidence of the rejected event |
| `topic`, `partition`, `offset`, `received_at` | as above | Same technical metadata as `raw_events` |
| `reason` | string | Technical validation failure reason (not a business judgement) |

`non-conforming/unknown` structural results are explicitly **not** routed to
`invalid_events` by this design: `docs/02-data-contract.md` states that
non-conforming does not automatically mean business-invalid. `invalid_events` is
reserved for objects that fail technical parsing/validation (e.g. malformed JSON),
which is a narrower condition than structural non-conformance. This distinction is
flagged as a decision that should be confirmed in an implementation spec, not
assumed here.

#### `processing_audit` (raw-side)

| Field | Type | Purpose |
|---|---|---|
| `raw_event_ref` | reference to `raw_events._id` (or `topic/partition/offset`) | Traceability to the source raw event |
| `stage` | string | Technical pipeline stage recorded |
| `status` | string | Outcome of that stage |
| `occurred_at` | datetime (UTC) | When the audit entry was recorded |

Exact relationship between this collection and the PostgreSQL `processing_audit`
table (same name, different zone) is `pending`: whether audit trail is duplicated,
split by stage, or unified is not decided by this spec.

### PostgreSQL: curated zone

All tables below are proposals. No column is derived from anything beyond the
apparent types recorded in `docs/02-data-contract.md`; every column not directly
backed by an observed field is marked `pending`.

#### `employees`

| Column | Type (proposed) | Notes |
|---|---|---|
| `id` | surrogate key (e.g. `BIGSERIAL`/UUID) | Candidate only; no business identity approved yet |
| `first_name` | `TEXT` | Sourced from observed `name` (variant E); canonical naming `pending` |
| `last_name` | `TEXT` | Sourced from observed `last_name` (variant E) |
| `sex` | `pending` | HRP-29 observed `sex` as a JSON array; representation (enum, array column, junction table) is `pending` until its content is understood |
| `telephone_number` | `TEXT` | Sourced from observed `telfnumber` (variant E); format unconfirmed |
| `email` | `TEXT` | Sourced from observed `email` (variant E); format unconfirmed |
| `passport` | `TEXT` | Correlation **candidate** only (variants C, E); not a confirmed unique/business key |
| `created_at`, `updated_at` | `TIMESTAMPTZ` | Standard curated audit columns |

No primary correlation key is defined. `passport` is listed as a column, not a
unique constraint, until a correlation rule is approved (see "Decisions requiring an
ADR" below).

#### `locations`

| Column | Type (proposed) | Notes |
|---|---|---|
| `id` | surrogate key | Candidate only |
| `employee_id` | FK → `employees.id` | Cardinality (1:1 vs 1:N per employee) is `pending`: HRP-29 shows `address`/`fullname` in both variant A and D, but does not establish whether these represent one location or multiple per person |
| `full_name` | `TEXT` | Sourced from observed `fullname` (variants B, D); correlation candidate only |
| `city` | `TEXT` | Sourced from observed `city` (variant D) |
| `address` | `TEXT` | Sourced from observed `address` (variants A, D); correlation candidate only |
| `ip_v4` | `TEXT` or `INET` | Sourced from observed `IPv4` (variant A); whether this belongs conceptually under "location" versus `network_data` is `pending` — kept here only because it co-occurs with `address` in variant A |

#### `professional_profiles`

| Column | Type (proposed) | Notes |
|---|---|---|
| `id` | surrogate key | Candidate only |
| `employee_id` | FK → `employees.id` | Cardinality `pending` |
| `full_name` | `TEXT` | Sourced from observed `fullname` (variant B); correlation candidate only |
| `company` | `TEXT` | Sourced from observed `company` (variant B) |
| `company_address` | `TEXT` | Sourced from observed `company address` (variant B) |
| `company_email` | `TEXT` | Sourced from observed `company_email` (variant B) |
| `company_telephone_number` | `TEXT` | Sourced from observed `company_telfnumber` (variant B) |
| `job` | `TEXT` | Sourced from observed `job` (variant B) |

#### `bank_accounts`

| Column | Type (proposed) | Notes |
|---|---|---|
| `id` | surrogate key | Candidate only |
| `employee_id` | FK → `employees.id` | Cardinality `pending` |
| `iban` | `TEXT` | Sourced from observed `IBAN` (variant C); format/validation `pending` |
| `passport` | `TEXT` | Correlation candidate only (variant C); duplicated with `employees.passport` intentionally until a join strategy is approved — see below |
| `salary` | `pending` (`NUMERIC` candidate) | HRP-29 observed `salary` as `string`; whether it is stored numeric or textual is `pending` until format is confirmed |

#### `network_data`

| Column | Type (proposed) | Notes |
|---|---|---|
| `id` | surrogate key | Candidate only |
| `employee_id` | FK → `employees.id` | Cardinality `pending` |
| `ip_v4` | `TEXT` or `INET` | Sourced from observed `IPv4` (variant A); see note under `locations` on the same field |

`network_data` and the `ip_v4` column under `locations` are listed as an open
duplication: HRP-29 observed `IPv4` only alongside `address` (variant A), so there is
no evidence forcing a separate `network_data` table versus folding it into
`locations`. Both options are documented; the final structure is `pending` a
correlation/grouping decision.

#### `processing_audit` (curated-side)

| Column | Type (proposed) | Notes |
|---|---|---|
| `id` | surrogate key | Candidate only |
| `employee_id` | FK → `employees.id`, nullable | Nullable because an audit entry may exist before a curated employee record does |
| `stage` | `TEXT` | Pipeline stage recorded (e.g. classification, upsert) |
| `status` | `TEXT` | Outcome of that stage |
| `raw_event_ref` | reference to the MongoDB raw event | Cross-zone traceability; exact reference format (`ObjectId` string vs. `topic/partition/offset` triple) is `pending` |
| `occurred_at` | `TIMESTAMPTZ` | When recorded |

### Idempotency constraints (curated zone)

No unique business constraint (e.g. on `passport`) is proposed for any curated table
in this design. `docs/02-data-contract.md` explicitly states that `passport`,
`fullname` and `address` are correlation *candidates* only, with no demonstrated
uniqueness. Declaring a `UNIQUE` constraint on any of them now would encode an
unapproved business rule into the schema. Idempotent upsert behaviour for curated
writes therefore remains `pending` a correlation-key decision, and must not be
designed around a default `ON CONFLICT (passport)`-style clause until that decision
is approved (candidate ADR — see below).

### Decisions requiring an ADR

| Decision | Why it needs an ADR | Status here |
|---|---|---|
| Person correlation key and conflict-resolution rule | Changes curated schema constraints, upsert behaviour and is hard to reverse once data is loaded | Not decided; see proposed ADR-0006 (Proposed, blocked on evidence) |
| Cardinality between `employees` and `locations`/`professional_profiles`/`bank_accounts`/`network_data` | Affects foreign-key design and query semantics across the API | Not decided; depends on the correlation-key ADR |
| Whether `network_data` is a separate table or folded into `locations` | Affects table count and join paths for the API | Not decided; depends on further Kafka evidence beyond HRP-29's single co-occurrence |
| Definitive downstream treatment of `non-conforming/unknown` events | Affects whether `process-worker` ever writes partial curated records | Not decided; `docs/02-data-contract.md` leaves it open |

### Decisions that only need a spec update (no ADR)

- Exact PostgreSQL column names and casing (cosmetic, reversible).
- Which technical `processing_status` enum values `raw_events` uses.
- Table/column comments and documentation wording.

## Acceptance criteria

- [ ] HRP-24 is confirmed merged into `develop` and used as the only source of
      structural facts for this design.
- [ ] The MongoDB collection design matches `docs/03-data-model.md`'s existing
      collection names and does not introduce a persisted business classification
      field on `raw_events`.
- [ ] Every proposed PostgreSQL column is traced to an observed field in
      `docs/02-data-contract.md` or explicitly marked `pending`.
- [ ] No unique or foreign-key constraint encodes an unapproved correlation rule.
- [ ] No mapping between variants A–E and Personal/Location/Professional/Bank/Net
      Data is introduced.
- [ ] Decisions requiring an ADR are listed, and no ADR here is marked `Accepted`.
- [ ] `docs/03-data-model.md` is updated to reference this design.
- [ ] No payload value, PII value, secret or generator reference appears anywhere in
      this document.
- [ ] The spec explicitly states it does not authorise SQL, Docker, ETL or API
      implementation, and names the future Jira tasks expected to carry that out.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Documentary | Every proposed column traces to an HRP-24/HRP-29 observed field or is marked `pending` | Manual cross-check against `docs/02-data-contract.md` |
| Traceability | Every table/collection references the spec section that justifies it | Manual review |
| Boundary review | No curated table stores a raw payload; no raw collection stores a resolved business record | Manual review against ADR-0002 |
| Security review | No payload value, PII, secret, `.env` content or generator reference | Manual review |
| Quality | `pre-commit run --all-files` | Command passes with no unrelated changes |
| Human review | Gaby reviews the documentary diff | Approval recorded in the PR before any next step |

## Closing evidence

- Branch / PR: `feature/HRP-25-modelo-datos` / pending.
- Commit: pending.
- Updated data model: pending (this PR).
- Validation commands and results: pending.
- Human reviewer approval: pending.
- Jira closing comment: pending; closure is not authorised by this draft.
