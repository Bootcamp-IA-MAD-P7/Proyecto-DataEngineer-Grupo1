# Data model

The detailed design—collections, tables, proposed columns, and the raw/curated
boundary—lives in [the HRP-25 specification](specs/HRP-25-modelo-datos.md). This
document is a concise summary. If there is a discrepancy, the HRP-25 specification
is the source of truth until an implementation task is approved.

## MongoDB: raw zone

Planned collections:

- `raw_events`: original event, Kafka metadata, receipt time, and processing state.
- `invalid_events`: an event that fails technical validation (not structural
  `non-conforming/unknown` classification), together with its reason.
- `processing_audit`: raw-side transformation and loading traceability.

The proposed technical duplicate-prevention index is `topic + partition + offset`.

Minimum proposed raw-event document:

| Field | Type | Purpose |
|---|---|---|
| `payload` | JSON object | Original evidence, without renaming or normalisation |
| `topic` | string | Kafka technical metadata |
| `partition` | integer | Kafka technical metadata |
| `offset` | integer | Kafka technical metadata |
| `received_at` | UTC datetime | Time at which the platform received the event |
| `processing_status` | technical string | Operational status, not a business classification |

Structural classification (A–E or `non-conforming/unknown`, as defined in
`docs/02-data-contract.md`) is not persisted as a `raw_events` field in this
design. It is a processing result, not a raw fact. The location for auditing that
classification remains pending (see HRP-25).

ADR-0005 proposes that the compound index be unique and that offset acknowledgement
occur only after a successful insertion or when MongoDB proves that the same
coordinates already exist. HRP-34 must validate this design with tests before the
proposal may be accepted; HRP-35 and HRP-36 must follow the final approved decision.
See [ADR-0005](adr/0005-kafka-acknowledgement-after-raw-persistence.md).

## PostgreSQL: curated zone

Planned tables, with candidate columns detailed in
[the HRP-25 specification](specs/HRP-25-modelo-datos.md):

- `employees`
- `locations`
- `professional_profiles`
- `bank_accounts`
- `network_data`
- `processing_audit`

No table currently includes a business unique constraint (for example, on
`passport`). `passport`, `fullname`, and `address` are correlation candidates
observed by HRP-29, not approved keys. The person correlation key, the cardinality
between `employees` and dependent tables, and the idempotent-upsert policy remain
pending in [ADR-0006](adr/0006-person-correlation-key.md), which stays `Proposed`
until additional evidence has received human review.

The final design will be approved in the relational-data-model Jira task after the
real-event contract is validated. HRP-25 does not authorise SQL, migrations, Docker,
ETL, or API code. Those are the responsibility of future Jira tasks—raw persistence,
ETL-to-PostgreSQL integration, and table creation—once the design has received human
review.
