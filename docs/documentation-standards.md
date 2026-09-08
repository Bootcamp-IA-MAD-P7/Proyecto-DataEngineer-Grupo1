---
description: Documentation, evidence and traceability standards for HR Pro Data Platform.
alwaysApply: true
---

# Documentation standards

## Source of truth and placement

| Need | Canonical location |
|---|---|
| Product scope and architecture | `docs/00-project-charter.md`, `docs/01-architecture.md` |
| Observed data contract | `docs/02-data-contract.md` plus `docs/observations/` |
| Data model | `docs/03-data-model.md` |
| Task specification | `docs/specs/HRP-XX-*.md` |
| Significant decision | `docs/adr/NNNN-*.md` |
| Daily progress | `docs/dailies/YYYY-MM-DD-*.md` |
| Presentation evidence | `docs/presentation-sources/NOTEBOOKLM-PACK.md` and `05-references.md` |
| Closeout acceptance vs evidence | `docs/delivery-evidence.md` |
| API and configuration | `docs/api-reference.md`, `docs/configuration.md` |
| Full navigation and review inventory | `docs/README.md`, `docs/documentation-audit.md` |
| AI task context | `docs/ai/task-packets/HRP-XX-*.md` |

## Writing rules

- Make claims traceable: distinguish observed facts, decisions and assumptions.
- Link a task spec to its Jira key, branch, PR, test/evidence and affected docs.
- Do not paste raw event payloads, secrets or personal data. Sanitise examples.
- Use concise headings, tables for repeated fields and Mermaid only when it clarifies
  a relationship.
- Update documentation in the same PR as the behaviour it describes.

## Specification minimum

Every implementation spec states: problem, scope/non-scope, dependencies, acceptance
criteria, design, error and security considerations, tests, evidence and rollback or
follow-up.

## Daily minimum

A daily records each contributor's completed work, evidence, blockers, next task and
decision needed. It records reality, not planned work presented as completed.

## Historical records and closeout

A reconstructed daily must name its reconstruction date and Git evidence. It cannot
invent meetings, blockers or personal approvals. Preserve original observations and
historical test results with their date and limits. Spec integration metadata may
supersede stale pending-merge text; do not tick old criteria automatically.

Keep owner acceptance separate from code presence, executed validation and
performance measurements. Presentation material must be self-contained enough to
read without resolving repository links; cite primary sources and do not load
historical draft templates as current evidence. A source pack is not a finished deck.

For documentation-only changes, check links, paths, numbers, evidence scope and Git
whitespace. Record that functional tests were not rerun rather than reporting success.
