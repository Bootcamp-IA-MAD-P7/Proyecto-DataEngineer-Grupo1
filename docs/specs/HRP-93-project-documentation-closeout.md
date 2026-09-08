# HRP-93 — Reconcile all project documentation for closeout

**Jira:** HRP-93
**Owner:** Miguel
**Status:** Documentation review authorised; current local revision
**Reviewers designated for PR:** Gaby and Johans, no approval asserted
**Code baseline:** f3a952b
**Remote documentation baseline:**275131a (PR #80)

## Objective

Deliver consistent, navigable documentation and self-contained NotebookLM sources,
covering every tracked Markdown document without changing runtime or inventing evidence.

## Scope

README, all Markdown guides, contracts, ADR status, spec integration metadata,
historical dailies, presentation sources, bibliography, source index and documentary
checks. Preserve original historical records and template semantics.
No application code, configuration, dependencies, data, frontend, benchmark, broker
observation, Jira transition, remote rules, push, merge or release publishing.

## Acceptance criteria

- [x] README separates owner acceptance from technical verification.
- [x] Runtime guides identify ingestion-only app, separate API and synthetic HRP-71.
- [x] Nine daily integration records include commits and retrospective labels.
- [x] NotebookLM has one self-contained package, a 12-slide narrative and references.
- [x] Historical specs include integration traceability without fabricated test results.
- [x] Frontend remains excluded; no secret or live payload is added.
- [x] All Markdown files are inventoried with review type and exceptions.

## Validation strategy

Local links/anchors and paths, duplicate/outdated claims, specification structure
and git whitespace check; results in [documentation audit](../documentation-audit.md).
Do not rerun functional tests or start services solely for this documentary change.
The owner's authorisation covers edits without an extra approval request and does
not change GitHub enforcement.

## Evidence and rollback

[Closeout](../project-closeout.md), [audit](../documentation-audit.md) and
[NotebookLM](../presentation-sources/NOTEBOOKLM-PACK.md).
This spec records the current change, not an already published release.
Revert only the identified documentation commit if required; preserve unrelated work.
