# HRP-94 — Define accessibility and sustainability policy

**Integration status (2026-09-08):** Task changes integrated in develop; acceptance criteria not re-executed here.
**Git evidence:** [0ec4fef](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/0ec4fef) / [PR #26](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/26) (2026-08-31).
**Closeout interpretation:** Accessibility/sustainability policy is integrated; it is not measured WCAG conformance, deployed frontend or quantified energy savings.

This integration record does not assert current Jira status, reviewer approval identity
or a new passing test run. [Current documentation](../README.md) and
[acceptance/evidence matrix](../delivery-evidence.md) define the closeout reading.

## Historical specification and task evidence

The scope, criteria, checkboxes and test results below are the task's original record.
They are not a live progress dashboard. Pending-review/merge references in this
historical record are superseded by the integration evidence above; unresolved
functional limitations are not automatically marked as passed.

**Original recorded status:** Ready for review

**Owner:** Miguel
**Jira:** HRP-94
**Dependencies:** Approved project direction; no runtime dependency
**Related ADR:** ADR-0007

## Objective

Establish an evidence-first policy that makes accessibility and sustainability
requirements actionable for future interface, API, delivery and infrastructure tasks.

## Context and scope

- Includes: ADR-0007, cross-cutting standards, SDD/spec/harness applicability gates,
  and targeted architecture/README corrections.
- Excludes: frontend implementation, JavaScript dependencies, AWS provisioning,
  Docker or API changes, carbon calculations and formal conformance claims.
- Verified assumptions: user-facing flows are future work; React + TypeScript + Vite
  is the preferred direction and Streamlit is fallback-only for a constrained demo.
- Risks: a policy can become documentation-only unless every applicable future spec
  records observable evidence and human review checks it.

## Design

ADR-0007 is the durable source for mandatory, conditional and deferred requirements.
`docs/base-standards.md` provides the short always-applicable rule, while the SDD,
spec template and harness require each applicable task to declare scope and evidence.
Architecture and README describe the direction as future, not deployed.

## Acceptance criteria

- [x] ADR-0007 distinguishes mandatory, conditional and deferred requirements without
  claiming unmeasured WCAG, carbon or AWS outcomes.
- [x] Future applicable specs must declare accessibility, sustainability and evidence
  or explain non-applicability.
- [x] Future user-facing flows target WCAG 2.2 AA with rendered-interface and keyboard
  validation.
- [x] Architecture and README no longer describe Streamlit as the sole selected
  frontend direction.
- [x] No frontend, AWS resource, dependency or runtime behaviour is introduced.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Documentation | Validate spec structure and links | Specification validator and diff review |
| Governance | Review standards and ADR boundaries | Human PR review by transformation and serving owners |
| Future UI | Rendered accessibility and keyboard validation | Deferred until a user-facing flow exists |

## Completion evidence

- Branch / PR: `docs/HRP-94-accessibility-sustainability-policy` / pending review
- Commit: pending
- Commands and result: pending local and GitHub Actions execution
- Jira closing comment: pending merge and human verification
