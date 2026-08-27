# HRP-29 — Observe and document Kafka messages

**Status:** Observation recorded; pending human review
**Owner:** Anahí (or a team member with authorised broker access)
**Jira:** HRP-29
**Dependencies:** HRP-28 completed
**Related ADR:** `docs/adr/0003-evidence-first-data-contract.md`

## Objective

Produce a sanitised, reproducible observation of real Kafka messages that allows the team to define a data contract without reading or analysing the educational data generator.

## Recorded evidence

The bounded observation is recorded in
`docs/observations/2026-08-27-HRP-29-kafka.md`. It records one observed topic,
one partition, a twenty-message structural sample and five distinct field sets
without retaining message values. The remaining unknowns stay visible in that
document for HRP-24.

## Scope and boundaries

- Includes: authorised broker connection, topic metadata, structural field observation, message-category detection, nullability, ordering, duplication and correlation candidates.
- Excludes: generator inspection, production consumer implementation, MongoDB persistence, data transformation and storing complete payloads.
- Assumption: HRP-28 confirms that the authorised connection can be established.
- Risk: a field, topic or correlation rule may remain unknown after a short observation and must then remain explicitly pending.

## Design

The observer creates a document from `docs/observations/_template.md` named `docs/observations/YYYY-MM-DD-HRP-29-kafka.md`. It records only metadata and a sanitised schema table. Values that could identify a person, address, account or contact are replaced with `<redacted>` or described as a pattern.

The observation document is the sole evidence that Gaby may use to update the data contract in HRP-24. README descriptions remain useful context but are not proof of the actual event shape.

## Acceptance criteria

- [x] An observation document records its observation date, topic, partitions and an approximate number of messages observed, without credentials. A precise time range was not retained and is explicitly out of scope for this sanitised evidence.
- [x] Categories, field names, types, nullability and safe structural examples are recorded without complete payloads or PII.
- [x] Potential correlation key, out-of-order messages, duplicates and incomplete groups are recorded as observed, not observed or pending.
- [x] The document confirms that the educational generator was not read, cloned or analysed.
- [ ] A PR links the document, passes quality checks and receives human review.
- [ ] HRP-24 is notified with the document and evidence link.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Manual | Connect through the authorised path | Successful connection or a documented blocker |
| Manual | Observe a bounded sample of messages | Sanitised structural table with topic metadata |
| Review | Inspect the observation document | No secrets, PII or generator material; facts separated from gaps |

## Completion evidence

- Branch / PR: `feature/HRP-29-kafka-observation-evidence` / PR #2
- Observation document: `docs/observations/2026-08-27-HRP-29-kafka.md`
- Commands or authorised tool used, without secrets: authorised metadata query and bounded in-memory observer
- Reviewer: Pending (Gaby)
- Jira closure comment:
