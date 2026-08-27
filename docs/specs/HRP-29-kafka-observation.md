# HRP-29 — Observe and document Kafka messages

**Status:** Ready for observation
**Owner:** Anahí (or a team member with authorised broker access)
**Jira:** HRP-29
**Dependencies:** HRP-28 completed
**Related ADR:** `docs/adr/0003-evidence-first-data-contract.md`

## Objective

Produce a sanitised, reproducible observation of real Kafka messages that allows the team to define a data contract without reading or analysing the educational data generator.

## Scope and boundaries

- Includes: authorised broker connection, topic metadata, structural field observation, message-category detection, nullability, ordering, duplication and correlation candidates.
- Excludes: generator inspection, production consumer implementation, MongoDB persistence, data transformation and storing complete payloads.
- Assumption: HRP-28 confirms that the authorised connection can be established.
- Risk: a field, topic or correlation rule may remain unknown after a short observation and must then remain explicitly pending.

## Design

The observer creates a document from `docs/observations/_template.md` named `docs/observations/YYYY-MM-DD-HRP-29-kafka.md`. It records only metadata and a sanitised schema table. Values that could identify a person, address, account or contact are replaced with `<redacted>` or described as a pattern.

The observation document is the sole evidence that Gaby may use to update the data contract in HRP-24. README descriptions remain useful context but are not proof of the actual event shape.

## Acceptance criteria

- [ ] An observation document records topic, timestamp range, partitions and an approximate number of messages observed, without credentials.
- [ ] Categories, field names, types, nullability and safe structural examples are recorded without complete payloads or PII.
- [ ] Potential correlation key, out-of-order messages, duplicates and incomplete groups are recorded as observed, not observed or pending.
- [ ] The document confirms that the educational generator was not read, cloned or analysed.
- [ ] A PR links the document, passes quality checks and receives human review.
- [ ] HRP-24 is notified with the document and evidence link.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Manual | Connect through the authorised path | Successful connection or a documented blocker |
| Manual | Observe a bounded sample of messages | Sanitised structural table with topic metadata |
| Review | Inspect the observation document | No secrets, PII or generator material; facts separated from gaps |

## Completion evidence

- Branch / PR:
- Observation document:
- Commands or authorised tool used, without secrets:
- Reviewer:
- Jira closure comment:
