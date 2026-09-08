# External implementation benchmark

## Reference and boundary

Historical comparison from 2026-08-28; the external repository was not re-inspected
for this closeout. This is not a performance benchmark or a current feature inventory.
Current implementation is described in [architecture](01-architecture.md).

- Reference: `Bootcamp-IA-MAD-P7/Proyecto1_modulo3_DE2`, branch `dev`, reviewed on
  2026-08-28 at commit `d42023c`.
- Purpose: compare delivery patterns and identify project-owned improvements.
- Boundary: this repository is not a dependency and its source code is not copied.
  No licence file was visible during the review, so only general engineering ideas and
  independently designed behaviour are used.
- The educational data generator remains out of scope and was not inspected.

## Patterns adopted into our design

| Pattern | Project-owned application |
|---|---|
| Batch raw writes | Flush by bounded size/time only after the HRP-34 repository contract exists |
| Healthchecks and non-root containers | Add per service during the Medium-level Docker slice |
| Structured and PII-safe logging | Central logging policy; never log payload or correlation values |
| Unit fakes plus real integrations | Fast unit suites and opt-in Docker integration suites |
| Operator-focused README | Commands, service map, evidence, limitations and current-vs-target state |
| Role-specific AI context | Keep tool-agnostic roles and task packets under `ai-specs/` and `docs/ai/` |

## Risks deliberately not inherited

| Observed risk | Our guardrail |
|---|---|
| Kafka acknowledgement can advance after a swallowed MongoDB failure | HRP-34 integrated in PR #33; ADR-0005 separates formal status from implemented durable acknowledgement |
| Raw documents lack complete Kafka identity and unique index | Required envelope and compound index |
| Business classification accepts partial field overlap | HRP-44 now classifies exact key sets; ADR-0006 bounds operational correlation |
| Dependencies are duplicated across files | `pyproject.toml` remains the Python dependency source of truth |
| Tests and lint are not enforced remotely | Versioned workflows and review policy; current remote enforcement not rechecked |
| Documentation and generated reports drift | Specs, evidence dates, PR references and evolving SWOT reviews |
| Expert extras overtake the required path | Essential, Medium, Advanced and Expert remain ordered milestones |

## Re-evaluation trigger

Revisit this benchmark after Essential is demonstrable. At that point compare raw
throughput, duplicate handling, restart behaviour, integration coverage and demo time;
do not compare only file counts or technology lists.
