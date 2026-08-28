# External implementation benchmark

## Reference and boundary

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
| Kafka acknowledgement can advance after a swallowed MongoDB failure | Proposed ADR-0005, pending HRP-34 failure-path integration tests and review |
| Raw documents lack complete Kafka identity and unique index | Required envelope and compound index |
| Business classification accepts partial field overlap | HRP-43 handles correlation; neutral variants remain until HRP-44 approves classification semantics |
| Dependencies are duplicated across files | `pyproject.toml` remains the Python dependency source of truth |
| Tests and lint are not enforced remotely | Required GitHub checks on every PR to `develop` |
| Documentation and generated reports drift | Specs, evidence dates, PR references and evolving SWOT reviews |
| Expert extras overtake the required path | Essential, Medium, Advanced and Expert remain ordered milestones |

## Re-evaluation trigger

Revisit this benchmark after Essential is demonstrable. At that point compare raw
throughput, duplicate handling, restart behaviour, integration coverage and demo time;
do not compare only file counts or technology lists.
