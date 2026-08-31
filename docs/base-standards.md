---
description: Canonical development rules for HR Pro Data Platform and every AI assistant.
alwaysApply: true
---

# Base standards

## 1. Core principles

- Work on one small, reviewable Jira task at a time.
- Specification before implementation: a task affecting code, data, infrastructure or
  operations needs a current spec and observable acceptance criteria.
- Tests and documentation change with behaviour; do not leave them for a later task.
- Prefer explicit types, descriptive names, dependency injection and bounded modules.
- Treat unknowns as unknowns. Record an assumption, discovery task or ADR instead of
  inventing a fact.
- New technical artifacts are written in English. Existing Spanish project material is
  preserved and may be translated incrementally in its own reviewed change.

## 2. Data, privacy and educational boundary

- Never inspect the educational generator's source code.
- Never commit credentials, `.env`, private broker addresses, full raw payloads,
  personal data, banking data or screenshots containing them.
- Only create test fixtures from authorised Kafka observation; minimise and sanitise
  them first.
- Preserve the raw/temporary/curated boundaries: MongoDB is raw evidence, Redis is
  temporary correlation state, and PostgreSQL is curated query data.

## 3. Delivery rules

1. Start from an updated `develop` branch and create one task branch.
2. Enrich the Jira task and create or update its spec before code.
3. Implement the smallest vertical slice: code, tests, docs and operational evidence.
4. Run `pre-commit run --all-files` and relevant `pytest` suites.
5. Open an English PR to `develop`; a different human reviews and approves it.
6. Merge only after checks, review and discussion resolution. Record verifiable
   evidence in Jira after merge.

## 4. Standards and reusable workflows

- `docs/backend-standards.md` — Python workers, data stores, APIs and testing.
- `docs/documentation-standards.md` — specifications, ADRs, dailies and evidence.
- `docs/development_guide.md` — local setup and daily workflow.
- `docs/data-model.md` — canonical data-model entry point.
- `ai-specs/agents/` — select the role matching the task.
- `ai-specs/skills/` — load the matching workflow before acting.

## 5. Completion gate

Do not call a task complete if its required spec, tests, documentation, PR review,
quality evidence or Jira closing note is missing.

## 6. Accessibility and sustainable delivery

- Every task that affects a user interface, API response, visualisation, deployment or
  resource use assesses its accessibility and sustainability applicability in its spec.
- Implemented user-facing flows target WCAG 2.2 AA. Use semantic HTML and native
  controls before WAI-ARIA; ARIA complements native semantics and does not replace
  them.
- Do not claim formal WCAG conformance, carbon neutrality, an SCI score, energy
  savings or AWS deployment without verifiable evidence for the implemented scope.
- Prefer the smallest dependency set and architecture that meet an approved need.
  Avoid duplicate processing or storage, unbounded retention, unnecessary transfer,
  aggressive polling and avoidable client work.
- Privacy, accessibility, security, maintainability and performance are complementary
  sustainability concerns. None may be weakened to optimise another.
- See ADR-0007 for mandatory, conditional and deferred requirements.
