# ADR-0005: Acknowledge Kafka only after durable raw persistence

## Status

Proposed — requires peer review with the HRP-34 implementation.

## Context

Kafka can redeliver an event when a consumer restarts or an acknowledgement is not
committed. MongoDB is the platform's raw system of record and must contain enough
transport metadata to distinguish a redelivery from a new event.

Acknowledging an event before MongoDB confirms the write can lose data. A generic
exception handler that hides a failed raw write and lets the consumer commit creates
the same risk. Conversely, refusing to acknowledge an already persisted event can
create an endless redelivery loop unless raw persistence is idempotent.

## Proposed decision

1. The raw envelope preserves the decoded JSON object without canonicalising its field
   names or values and adds `topic`, `partition`, `offset` and `received_at`.
2. MongoDB has a unique compound index on `topic`, `partition` and `offset`.
3. The consumer acknowledges an event only after MongoDB reports either:
   - a successful insert; or
   - an existing document with the same Kafka coordinates.
4. A timeout, connection failure or unclassified persistence error leaves the offset
   uncommitted and emits technical-only logs and a failure metric.
5. Classification, correlation and curated persistence happen after the raw boundary.
   Their failure must not mutate or delete the raw event.
6. Batch writers return the exact coordinates durably persisted before the caller can
   advance the committed offset.

## Expected consequences if accepted

- The raw path provides at-least-once delivery with idempotent storage.
- Reprocessing can start from MongoDB without reading the educational producer.
- Storage failures may temporarily reduce throughput but do not silently discard data.
- HRP-34, HRP-35 and HRP-36 must be designed and tested together at their boundary,
  while remaining separate Jira deliverables.

## Required evidence

- Duplicate Kafka coordinates produce one raw document.
- A MongoDB write failure does not commit the Kafka message.
- A successful insert permits a commit.
- Logs contain transport metadata and error type, never payload values.
- Restarting the worker does not produce observable loss or duplicate raw events.

## Acceptance gate

The status may change from `Proposed` to `Accepted` only after HRP-34 provides the
required failure-path and idempotency evidence and a peer reviewer explicitly approves
the ingestion/storage boundary. The review reference and date must be added here when
that happens. Until then, surrounding documentation must describe this policy as a
proposal rather than an implemented invariant.
